"""Asynchronous callers use these bounded HTTP operations. Never guesses a city."""
from __future__ import annotations
import math
import requests

def geocode(city):
    city=str(city).strip()
    if not city:raise ValueError('Informe uma cidade.')
    r=requests.get('https://geocoding-api.open-meteo.com/v1/search',
                   params={'name':city[:120],'count':8,'language':'pt','format':'json'},timeout=(4,8))
    r.raise_for_status();out=[]
    for item in r.json().get('results',[]):
        lat=float(item['latitude']);lon=float(item['longitude'])
        if not (-90<=lat<=90 and -180<=lon<=180):continue
        out.append({'label':', '.join(filter(None,[item.get('name'),item.get('admin1'),item.get('country')])),
                    'latitude':lat,'longitude':lon})
    if not out:raise ValueError('Cidade não encontrada. Tente o nome completo.')
    return out

def fetch_weather(latitude,longitude):
    lat=float(latitude);lon=float(longitude)
    if not (math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
        raise ValueError('Coordenadas inválidas.')
    r=requests.get('https://api.open-meteo.com/v1/forecast',params={
        'latitude':lat,'longitude':lon,'timezone':'auto',
        'current':'temperature_2m,apparent_temperature,is_day,weather_code,cloud_cover,wind_speed_10m,relative_humidity_2m'},
        timeout=(4,8))
    r.raise_for_status();data=r.json();cur=data['current']
    return {'temperature':float(cur['temperature_2m']),'feels':float(cur['apparent_temperature']),
            'day':bool(cur['is_day']),'code':int(cur['weather_code']),
            'cloud':float(cur['cloud_cover']),'wind':float(cur['wind_speed_10m']),
            'humidity':float(cur['relative_humidity_2m']),'time':str(cur['time']),
            'timezone':str(data.get('timezone',''))}

def condition(code):
    if code==0:return 'Céu limpo'
    if code in (1,2):return 'Parcialmente nublado'
    if code==3:return 'Nublado'
    if code in (45,48):return 'Nevoeiro'
    if code in (95,96,99):return 'Tempestade'
    if code in (71,73,75,77,85,86):return 'Neve'
    if code in (51,53,55,56,57):return 'Garoa'
    if code in (61,63,65,66,67,80,81,82):return 'Chuva'
    return 'Condição indisponível'
