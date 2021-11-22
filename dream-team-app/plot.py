from matplotlib import pyplot as plt
import io
import base64

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure




def createFigure(valuesX, valuesY, title, xLabel, yLabel, color, type):

    #Generera figuren
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title(title)
    axis.set_xlabel(xLabel)
    axis.set_ylabel(yLabel)
    axis.grid()
    if type == "plot":
        axis.plot(valuesX, valuesY, color+"-")
    elif type == "barh":
        axis.barh(valuesX, valuesY, color=color)
        fig.set_size_inches(12, 5)
 
    #Konvertera figur till PNG
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)

    #Konvertera PNG till base64
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    return pngImageB64String


def monthlyAvgPlotter(dict):
    months = []
    averages = []

    for value in dict.values():
        averages.append(value[0])
        months.append(value[3])

    return createFigure(months, averages, "Average monthly value for the won deals", "Months", "", "go", "plot")


def piechart(labels, sizes, title):
    
    explode = (0.2, 0, 0, 0)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    axis.set_title(title)
    axis.pie(sizes, labels=labels, explode=explode, autopct='%1.1f%%',shadow=True, startangle=90)

    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)

    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')

    return pngImageB64String



    
    

