from flask import Flask, render_template
import requests
import json
import datetime
import dateutil.parser
import helper
import plot
import certifi
import urllib3


app = Flask(__name__, static_url_path='/static')

headers = {
    "Content-Type": "application/json",
    "Accept": "application/hal+json",
    "x-api-key": ""
}


def get_api_data(headers, url):
    """
    response = requests.get(url=url,
                            headers=headers,
                            data=None,
                            verify=False)

    """
    http = urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED",
        ca_certs=certifi.where()
    )

    response = http.request("GET", url=url,
                            headers=headers)
    print(type(response))
    # Convert response string into json data and get embedded limeobjects
    json_data = json.loads(response.data)
    limeobjects = json_data.get("_embedded").get("limeobjects")

    # Check for more data pages and get thoose too

    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]
        """
        response = requests.get(url=url,
                                headers=headers,
                                data=None,
                                verify=False)
        """

        response = http.request("GET", url=url,
                                headers=headers)

        json_data = json.loads(response.data)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")

    return limeobjects


def getDealResponse():
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params1 = "?_limit=50&_sort=closeddate&_embed=company&"
    params2 = "max-closeddate=2020-12-31T23:59Z&min-closeddate=2020-01-01T00:00Z&dealstatus=agreement"
    url = base_url + params1 + params2
    response_deals = get_api_data(headers=headers, url=url)
    return response_deals


# Index page
@app.route('/')
def index():
    return render_template('home.html')


"""
Routes to the "/average" page- calculates the average won deal value for the filtered time period in 
the method getDealResponse, visualizes the data in a plot
"""


@app.route('/average')
def average():
    response_deals = getDealResponse()

    if len(response_deals) == 0:
        msg = 'No deals found'
        return render_template('average.html', msg=msg)

    sum = 0
    value_month_dict = {}

    for item in response_deals:
        value = item['value']
        sum += value
        input_dt = item['closeddate']
        dt_object = dateutil.parser.isoparse(input_dt)
        month = dt_object.month
        value_month_dict[month] = value

    result = helper.avg(sum, len(response_deals))

    pngImageB64String = plot.createFigure(list(value_month_dict.keys()), value_month_dict.values(
    ), "Total values for the won deals throughout last year", "Months", "Value", "b", "plot")

    return render_template('average.html',  avg=round(result), image=pngImageB64String)


"""
Routes to the "/avgpermonth" page- calculates the average won deal value and number of won deals per month
for the filtered time period in the method getDealResponse,
visualizes the data in a plot
"""


@app.route('/avgpermonth')
def avgpermonth():
    response_deals = getDealResponse()

    if len(response_deals) == 0:
        msg = 'No deals found'
        return render_template('average.html', msg=msg)

    dict = {}

    for item in response_deals:
        input_dt = item['closeddate']
        dt_object = dateutil.parser.isoparse(input_dt)
        month = dt_object.month
        if not month in dict:
            dict[month] = [1, item['value']]
        else:
            dict[month][0] += 1
            dict[month][1] += item['value']

    monthly_avg = helper.calcMonthlyAvg(dict)
    pngImageB64String = plot.monthlyAvgPlotter(monthly_avg)

    return render_template('avgpermonth.html',  monthly_avg=monthly_avg, image=pngImageB64String)


"""
Routes to the "/valuepercustomer" page- calculates the average won deal value per customer for the filtered time period 
in the method getDealResponse, visualizes the data in a plot
"""


@app.route('/valuepercustomer')
def valuepercustomer():
    response_deals = getDealResponse()

    if len(response_deals) == 0:
        msg = 'No deals found'
        return render_template('average.html', msg=msg)

    customer_dict = {}

    for item in response_deals:
        company_name = item['_embedded']['relation_company']['name']
        value = item['value']
        if not company_name in customer_dict:
            customer_dict[company_name] = value
        else:
            customer_dict[company_name] += value

    pngImageB64String = plot.createFigure(list(customer_dict.keys()), customer_dict.values(
    ), "Total values for won deals per customer", "Total value(SEK)", "", "b", "barh")

    return render_template("valuepercustomer.html", customer_list=customer_dict, image=pngImageB64String)


"""
Routes to the "/updatecompanystatus" page- calculates the status for the companies in the lime server
according to the following requirements:
-A company which has bought anything the past year should be a "customer"
-A company which has never bough anything should be considered a "prospect" unless it 
has the status "notinterested"
-A company which has bought something in the past. but not the last year should be 
classified as "inactive"
"""


@app.route('/updatecompanystatus')
def updatecompanystatus():
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/?_limit=50"
    url = base_url
    response_companies = get_api_data(headers=headers, url=base_url)

    if len(response_companies) == 0:
        msg = 'No companies found'
        return render_template('average.html', msg=msg)

    id_dict = {}
    for item in response_companies:
        id_dict[item['_id']] = [item['name'],
                                item['buyingstatus']['key'] == "notinterested"]

    status_dict = {}
    status_distribution = [0, 0, 0, 0]
    url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/?_limit=50&_sort=-closeddate&_embed=company"
    response_id_deals = get_api_data(headers=headers, url=url)

    if len(response_id_deals) <= 0:
        msg = 'No deals found'
        return render_template('average.html', msg=msg)

    current_time = datetime.datetime.now()
    year_min = current_time.replace(year=current_time.year-1).isoformat()

    for item in response_id_deals:
        company_id = item['company']
        last_buy_date = item['closeddate']
        if company_id in id_dict and last_buy_date != None:
            if last_buy_date > year_min:
                status_dict[id_dict[company_id][0]] = "Customer"
                status_distribution[0] = status_distribution[0]+1
            else:
                status_dict[id_dict[company_id][0]] = "Inactive"
                status_distribution[1] = status_distribution[1]+1
            del id_dict[company_id]

    for values in id_dict.values():
        if values[1]:
            status_dict[values[0]] = "Not interested"
            status_distribution[2] = status_distribution[2]+1
        else:
            status_dict[values[0]] = "Prospect"
            status_distribution[3] = status_distribution[3]+1

    pngImageB64String = plot.piechart(
        ["Customer", "Inactive", "Not interested", "Prospect"], status_distribution, "Status distribution")

    return render_template('updatecompanystatus.html', status_list=status_dict, image=pngImageB64String)


@app.route('/myroute')
def myroute():
    mydata = [{'name': 'apple'}, {'name': 'mango'}, {'name': 'banana'}]
    """
    For mytemplate.html to rendered you have to create the mytemplate.html
    page inside the templates-folder. And then add a link to your page in the
    _navbar.html-file, located in templates/includes/
    """
    return render_template('mytemplate.html', items=mydata)


# DEBUGGING
"""
If you want to debug your app, one of the ways you can do that is to use:
import pdb; pdb.set_trace()
Add that line of code anywhere, and it will act as a breakpoint and halt
your application
"""

if __name__ == '__main__':
    app.secret_key = 'somethingsecret'
    app.run(debug=True)
