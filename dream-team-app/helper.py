# -*- coding: utf-8 -*-
import datetime


def avg(num, dem):
    return num/dem


def calcMonthlyAvg(dict):
    temp = {}
    for key in dict:
        month_num = key
        names = convertToMonthname(month_num)
        temp[key] = [avg(dict[key][1], dict[key][0]), dict[key][0],
                     names[0], names[1]]
    return temp


def convertToMonthname(month_num):
    datetime_object = datetime.datetime.strptime(str(month_num), "%m")
    month_name_long = datetime_object.strftime("%B")
    month_name_short = datetime_object.strftime("%b")
    return month_name_long, month_name_short
