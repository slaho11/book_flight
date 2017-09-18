#!/usr/bin/env python

# author: Matej Slahucka, slahucka11@gmail.com
# date: 13.7.2017
# tested with python 3.5.3 on Debian 9

# Find and book flight(s) using skypicker.com API. 
# For further information see: https://gist.github.com/martin-kokos/d578679d97eb1652dfeb3e7f2a4e115b'

# How does this script work?
# 
# All the job is done in function main() in few steps
# 1: parsing arguments, module argparse
# 2: searching for flights, module requests, line 136.
#   cheapest/shortest flight is found by sending sort=price/duration in URL as part of http get request
#   and then simply using the first flight from response, data[0].
#   I'm not sure if this is a correct solution. Script works same as kiwi.com suggestions 
#   for cheapest/shortest flight, but sometimes even cheaper flights are listed bellow and I'm not sure why.
# 3: booking the flight and printing PNR number, line 175.

# NOTE: To see details about booked flight uncomment line 154.

import requests
import json
from datetime import datetime
from datetime import timedelta
import argparse
import sys

# this function print basic information about the first flight in dic, data[0]
# dic = response returned by skypicker.com/flights
def print_flight(dic):

  # print all the routes
  for elem in dic['data'][0]['route']:
    print('\t{} ({}) --> {} ({}) \t'.format(elem['cityFrom'], elem['flyFrom'], elem['cityTo'], elem['flyTo']))    
  
  # get the total flight duration in seconds
  duration = dic['data'][0]['duration']['total']
  # convert seconds to hh:mm:ss format
  duration = str(timedelta(seconds=duration))
  # remove last 3 characters, so we get time in hh:mm format
  duration = duration[:-3]

  print('\n\tFlight Duration: {}'.format(duration))
  print('\tPrice: {} {}\n'.format(dic['data'][0]['price'], dic['currency'])) 

# function main
def main():

  # set the argument parser
  argParser = argparse.ArgumentParser(
    usage = '%(prog)s --date yyyy-mm-dd --from code --to code [--shortest] [--cheapest] [--one-way] [--return n]',
    description = '''Find and book flight(s) using skypicker.com API. See:
                https://gist.github.com/martin-kokos/d578679d97eb1652dfeb3e7f2a4e115b''')

  argParser.add_argument('--date', dest='date', metavar='yyyy-mm-dd', required=True, 
    type=lambda x: datetime.strptime(x, '%Y-%m-%d').date(),
    help='Departure date. Format: YYYY-mm-dd')
  argParser.add_argument('--from', dest='frm', metavar='code', required=True,
    help='IATA code of the departure destination. For example: PRG, VIE, BUD ...')
  argParser.add_argument('--to', dest='to', metavar='code' ,required=True,
    help='IATA code of the arrival destination. For example: BKK, MIA, DPS ...')

  # create mutually exclusive group so arguments --cheapest and --shortest cannot be combined together
  # --cheapest = book the cheapest flight
  # --shortest = book the shortest flight
  searchByGroup = argParser.add_mutually_exclusive_group()
  searchByGroup.add_argument('--shortest', action='store_true', default=False, dest='shortest',
   help='Find the shortest flight in terms of flight duration. This argument cannot be combined with --cheapest.')
  searchByGroup.add_argument('--cheapest', action='store_true', default=True, dest='cheapest',
    help='Find the cheapest flight. This argument cannot be combined with --shortest.')

  # create mutually exclusive group so arguments --return and --one-way cannot be combined together
  # --return = round
  # --one-way = oneway
  typeFlightGroup = argParser.add_mutually_exclusive_group()
  typeFlightGroup.add_argument('--return', metavar='n', dest='round', type=int,
    help='''Find return flight. Variable n indicates number of days in the destination.
    This argument cannot be combined with --one-way.''')
  typeFlightGroup.add_argument('--one-way', action='store_true', default=True, dest='oneWay',
    help='Find one way flight. This argument cannot be combined with --return n.')  

  # parse the arguments
  arg = argParser.parse_args()

  # variables declaration
  # cities, from --> to
  flyFrom = None
  to = None

  # daterange for the flight departure
  dateFrom = None
  dateTo = None

  # days range for the length of stay at destination
  daysInDestinationFrom = None
  daysInDestinationTo = None

  typeFlight = None
  sort = None  

  # set the variables 
  if arg.date:
    # convert date format from yyyy-mm-dd to dd/mm/yyyy
    dateFrom = datetime.strftime(arg.date, '%d/%m/%Y')
    dateTo = dateFrom

  # city from
  if arg.frm:
    flyFrom = arg.frm.upper()

  # city to
  if arg.to:
    to = arg.to.upper()

  # return and date range
  if arg.round:
    typeFlight = 'round'
    daysInDestinationFrom = arg.round
    daysInDestinationTo = arg.round

  # one-way
  elif arg.oneWay:
    typeFlight = 'oneway'

  if arg.shortest:
    sort = 'duration'

  elif arg.cheapest:
    sort = 'price'

  # URL parameters
  # if the value is None parameter is not added 
  payload = {'flyFrom': flyFrom, 'to': to, 'dateFrom': dateFrom, 'dateTo': dateTo, 
              'daysInDestinationFrom': daysInDestinationFrom, 'daysInDestinationTo': daysInDestinationTo,
              'typeFlight': typeFlight, 'sort': sort}

  # find the flights
  req_flights = requests.get('https://api.skypicker.com/flights', params=payload)
  # print(req_flights.url)

  # check http return code 
  if int(req_flights.status_code) != requests.codes.ok:
    print('Something went wrong while searching for flights. Server has returned code {}.'.format(req.status_code))
    print(req_flights.text)
    sys.exit(1)

  # convert the response to Python dictionary
  req_flights = req_flights.json()
  
  # check how many flights have been found
  if int(req_flights['_results']) == 0:
    print(r'No flights have been found. Please change dates and/or check correctness of IATA airports codes.')
    sys.exit(0)

  # print information about flight(first returned, data[0])
  # print_flight(req_flights)  

  # values for booking request
  booking_token = req_flights['data'][0]['booking_token']  
  values = {
    'passengers': [
      {
        'firstName': 'Matej',
        'lastName': 'Slahucka',
        'title': 'Mr',
        'birthday': '1900-01-01',
        'email': 'slahucka11@gmail.com',
        'documentID': '4815162342'
      }
    ],
    'currency': 'EUR',
    'booking_token': booking_token
  }
  
  # post the data and get the response
  req_booking = requests.post('http://37.139.6.125:8080/booking', json=values)

  # print(req_booking.url)

  # check http return code 
  if int(req_booking.status_code) != 200:
    print('Something went wrong while booking the flight. Server has returned code {}.'.format(req_booking.status_code))
    print(req_booking.text)
    sys.exit(1)

  # convert to Python dict
  req_booking = req_booking.json()
  # print PNR number returned by server
  print('PNR: {}'.format(req_booking['pnr']))


if __name__ == '__main__':
  main()