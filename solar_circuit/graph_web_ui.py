import time
import logging
import os
import os.path
import json
from circuits.web.wsgi import Gateway
from circuits.web import Controller, Server
from circuits.io.events import stopped
from circuits import Event


from solar_circuit.libs.pyhighcharts import Chart, ChartTypes
from solar_circuit.libs.pyhighcharts.chart import SHOW_TEMPLATE
from solar_circuit.libs.tinydb import Query
from solar_circuit.sample_database import get_database
from solar_circuit.utility.helpers import ts_hours_ago, ts_to_dt, str_to_color


class do_exit(Event):
	pass

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
		curr = get_database().cursor()
		curr.execute("SELECT DISTINCT dev_id FROM samples")
		for t in curr.fetchall():
			ret += '<a href="/graphdevice/{0}">{0}</a><br/>'.format(t[0])

		ret += "<br /><br />"

		curr.execute("SELECT DISTINCT channel FROM samples")
		for t in curr.fetchall():
			ret += '<a href="/graphchannel/{0}">{0}</a><br/>'.format(t[0])

		ret += '<br/><br/><a href="/exit">Exit</a>'
		return ret

	def graphdevice(self, dev_id, hours=24):
		logging.info("Graphing %s from the last %s hours", dev_id, hours)

		chart = Chart(title={'text':dev_id},
				  yAxis={'title': {'text': 'Value'}},
				  xAxis={'type': 'datetime'})
		curr = get_database().cursor()
		try:
			curr.execute("SELECT * FROM samples WHERE dev_id=? AND utc > datetime('now', '-{} hours') ORDER BY utc ASC".format(hours),
						 (dev_id,))
			resp = curr.fetchall()
		except Exception as e:
			logging.exception(e)
		serieses = {}

		for s in resp:
			if s[3] not in serieses:
				serieses[s[3]] = []
			serieses[s[3]].append((s[2], s[4]))

		for s in serieses:
			chart.add_data_series(ChartTypes.line, serieses[s], name=s,
								  visible=(s in self.DEFAULTS),
								  animation=(s not in self.DEFAULTS),
								  marker={'enabled': False},
								  color=str_to_color(s))

		return SHOW_TEMPLATE.safe_substitute(container=chart.container,
											  chart=chart.script())

	def graphchannel(self, channel, hours=24):
		logging.info("Graphing %s from the last %s hours", channel, hours)

		chart = Chart(title={'text':channel},
				  yAxis={'title': {'text': 'Value'}},
				  xAxis={'type': 'datetime'})
		curr = get_database().cursor()

		curr.execute("SELECT * FROM samples WHERE channel=? AND utc > datetime('now', '-{} hours') ORDER BY utc ASC".format(hours),
					 (channel,))
		resp = curr.fetchall()
		serieses = {}

		for s in resp:
			if s[1] not in serieses:
				serieses[s[1]] = []
			serieses[s[1]].append((s[2], s[4]))

		for s in serieses:
			chart.add_data_series(ChartTypes.line, serieses[s], name=s,
								  visible=(s in self.DEFAULTS),
								  animation=(s not in self.DEFAULTS),
								  marker={'enabled': False},
								  color=str_to_color(s))

		return SHOW_TEMPLATE.safe_substitute(container=chart.container,
											  chart=chart.script())

	def exit(self):
		logging.critical("Exit command recieved")
		self.fire(stopped())
		self.fire(do_exit())
		return "Exiting..."

	def do_exit(self):
		raise SystemExit(0)


WebUIServer = Server(("0.0.0.0", 10000))
WebUI().register(WebUIServer)
# Gateway({"/foo": foo}).register(WebUIServer)
