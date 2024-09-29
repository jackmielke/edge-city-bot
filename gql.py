import json
from datetime import datetime
from pytz import timezone
from dateutil import parser
import requests

utc = timezone("UTC")
pdt = timezone('US/Pacific')

def get_events(args):
	print(args)
	start_time_str = None
	if args["start_time"]:
		start_time_str = "start_time: {_lte: \"" + args["start_time"] + "\"}"
	end_time_str = "end_time: {_gte: \"" + (args["end_time"] if "end_time" in args else datetime.now().isoformat()) + "\"}"
	limit = 20
	if "limit" in args and args["limit"] < 20 and args["limit"] > 0:
		limit = args["limit"]
	limit_str = f"limit: {limit}"
	graphql_url = "https://graph.sola.day/v1/graphql"
	graphql_query = """query MyQuery  {
	events (where: {""" + end_time_str + """,
	"""+ (start_time_str if start_time_str else "") + """
	group_id: {_eq: 3463},
	status: {_in: ["open", "new", "normal"]}}
	order_by: {end_time: asc},""" + limit_str + """
	offset: 0) {
	formatted_address
	start_time
	title
	end_time
	content
	location
	}
	}"""

	print(graphql_query)
	response = requests.post(
		graphql_url,
		json={'query': graphql_query}
	)

	result = response.json()
	events = result["data"]["events"]

	with open("response.json", "w") as f:
		json.dump(events, f, indent=4, sort_keys=True)

	for e in events:
		for key in e:
			try:
				naive_dt = parser.isoparse(e[key])
				utc_dt = utc.localize(naive_dt)
				e[key] = utc_dt.astimezone(pdt).strftime("%Y-%m-%d %H:%M")
			except ValueError:
				pass
			except TypeError:
				pass

	return events
