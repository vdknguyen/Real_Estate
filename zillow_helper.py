import urllib2
import json
import xmltodict

def get_zillow_data(address,city,state,zip_code):
    zillow_data = {}
    zws_id = 'X1-ZWz1f3zo3l3pjf_60bkd' # zillow webservice id
    link = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?zws-id=%s&address=%s&citystatezip=%s&rentzestimate=True'%(zws_id,address,zip_code)

    file = urllib2.urlopen(link)
    data = file.read()
    file.close()

    zillow_zestimates = xmltodict.parse(data)
    zillow_data['zestimate'] = float(zillow_zestimates['SearchResults:searchresults']['response']['results']['result']['zestimate']['amount']['#text'])
    zillow_data['rent_zestimate'] = float(zillow_zestimates['SearchResults:searchresults']['response']['results']['result']['rentzestimate']['amount']['#text'])

    link = 'http://www.zillow.com/webservice/GetRateSummary.htm?zws-id=%s&state=%s'%(zws_id,state)
    file = urllib2.urlopen(link)
    data = file.read()
    file.close()

    zillow_rates = xmltodict.parse(data)
    zillow_data['thirty_year_rate'] = float(zillow_rates['RateSummary:rateSummary']['response']['today']['rate'][0]['#text'])
    zillow_data['fifteen_year_rate'] = float(zillow_rates['RateSummary:rateSummary']['response']['today']['rate'][1]['#text'])
    return zillow_data
    