import time
import logging
import os
import os.path
import json
from circuits.web.wsgi import Gateway
from circuits.web import Controller, Server


from solar_circuit.libs.pyhighcharts import Chart, ChartTypes
from solar_circuit.libs.pyhighcharts.chart import SHOW_TEMPLATE
from solar_circuit.libs.tinydb import Query
from solar_circuit.sample_database import get_database
from solar_circuit.utility.helpers import ts_hours_ago, ts_to_dt


# def foo(environ, start_response):
	# start_response("200 OK", [("Content-Type", "text/plain")])
	# return ["Foo!"]


class WebUI(Controller):
	DEFAULTS = ['Power']
	def __init__(self):
		super(WebUI, self).__init__()
		self.database = None
	
	def database_ready(self, database):
		logging.info(database)

	def index(self):
		ret = ""
		for t in [_ for _ in get_database().tables()]:
			ret += '<a href="/graph/{0}">{0}</a><br/>'.format(t)
		return ret
		
	def graph(self, table, hours=24):
		Sample = Query()
		table = get_database().table(table)
		chart = Chart(title={'text':"Measurements"},
				  yAxis={'title': {'text': 'Value'}},
				  xAxis={'type': 'datetime'})
		
		samples = table.search(Sample.utc.test(ts_hours_ago, int(hours)))
		samples.sort(key=lambda x: ts_to_dt(x['utc']))
		
		serieses = {}
		
		for s in samples:
			if s['channel'] not in serieses:
				serieses[s['channel']] = []
			ts = ts_to_dt(s['utc'])
			serieses[s['channel']].append((ts, s['value']))
		
		for s in serieses:
			chart.add_data_series(ChartTypes.line, serieses[s], name=s, 
								  visible=(s in self.DEFAULTS),
								  marker={'enabled': False})
		
		return SHOW_TEMPLATE.safe_substitute(container=chart.container,
											  chart=chart.script())
		
	def exit(self):
		raise SystemExit(0)


WebUIServer = Server(("0.0.0.0", 10000))
WebUI().register(WebUIServer)
# Gateway({"/foo": foo}).register(WebUIServer)
