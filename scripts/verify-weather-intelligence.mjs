import assert from 'node:assert/strict';
import {weatherSummaryFromOpenMeteo,windDirectionLabel} from '../server/siteContext.mjs';
import {assessWeather,summarizeLocation,estimateRisk} from '../src/ai/intelligence.ts';

assert.equal(windDirectionLabel(0),'N');
assert.equal(windDirectionLabel(45),'NE');
assert.equal(windDirectionLabel(180),'S');
assert.equal(windDirectionLabel(270),'W');
assert.equal(windDirectionLabel(null),null);

const provider={
  current:{
    time:'2026-09-28T20:00',
    temperature_2m:34.2,
    relative_humidity_2m:27,
    precipitation:0,
    rain:0,
    wind_speed_10m:28,
    wind_direction_10m:48,
    wind_gusts_10m:43,
  },
  hourly:{
    temperature_2m:[34,33,32],
    relative_humidity_2m:[27,24,31],
    precipitation:[0,0.2,0],
    rain:[0,0.2,0],
    wind_speed_10m:[28,31,26],
    wind_direction_10m:[48,50,45],
    wind_gusts_10m:[43,48,41],
  },
};
const weather=weatherSummaryFromOpenMeteo(provider);
assert.equal(weather.temperatureC,34.2);
assert.equal(weather.humidityPercent,27);
assert.equal(weather.windDirectionLabel,'NE');
assert.equal(weather.forecast24h.minHumidityPercent,24);
assert.equal(weather.forecast24h.maxWindKph,31);
assert.equal(weather.forecast24h.rainTotalMm,0.2);

const malformed=weatherSummaryFromOpenMeteo({current:{temperature_2m:'bad'},hourly:{rain:['x']}});
assert.equal(malformed,null,'Malformed provider values must not become fake zeroes');

const dryContext={landCover:'forest',industrialDistanceKm:5,windKph:28,weather:{...weather,source:'Open-Meteo'}};
const dry=assessWeather(dryContext);
assert.ok(dry.points>0);
assert.ok(dry.points<=15,'Weather contribution must be capped');
assert.match(dry.summary,/increase spread concern|dry-condition context/i);

const wetWeather={...weather,humidityPercent:80,rainMm:10,precipitationMm:10,windKph:5,windGustKph:8};
const wet=assessWeather({...dryContext,windKph:5,weather:wetWeather});
assert.ok(wet.points<dry.points);
assert.match(wet.summary,/reduce immediate vegetation fire-spread concern/i);

const noWeather=assessWeather({landCover:'unknown',industrialDistanceKm:null,windKph:null});
assert.equal(noWeather.points,0);
assert.deepEqual(noWeather.missing,['Weather unavailable']);

const selected={id:'3',latitude:21,longitude:79,observedAt:'2026-09-28T12:00:00.000Z',frp:60,source:'manual'};
const rows=[
  {id:'1',latitude:21,longitude:79,observedAt:'2026-09-26T12:00:00.000Z',frp:10,source:'manual'},
  {id:'2',latitude:21,longitude:79,observedAt:'2026-09-27T12:00:00.000Z',frp:20,source:'manual'},
  selected,
];
const history=summarizeLocation(selected,rows);
const predictions=estimateRisk(history,dryContext,null);
assert.equal(predictions.length,3);
assert.ok(predictions[0].contributingFactors.some(f=>/Weather context/.test(f.label)));
assert.ok(predictions[0].riskScore>=0&&predictions[0].riskScore<=100);

console.log('PASS: Open-Meteo parsing, wind labels, 24h aggregation, missing-data safety, capped weather context and risk integration.');
