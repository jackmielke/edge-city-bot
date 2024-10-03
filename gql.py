import json
from datetime import datetime
from pytz import timezone
from dateutil import parser
import requests

utc = timezone("UTC")
pdt = timezone('US/Pacific')

def get_events(args):
	print(args)
	group_id = 3463
	start_time_str = None
	if args["start_time"]:
		# start_time_str = str(args["start_time"].date())
		# end_time_str = str(args["end_time"].date())
		start_time_str = args["start_time"][0:10]
		end_time_str = args["end_time"][0:10]
		query_url = f"https://prodnet.sola.day/api/event/list?group_id={group_id}&start_date={start_time_str}&end_date={end_time_str}"
	else:
		query_url = f"https://prodnet.sola.day/api/event/list?group_id={group_id}"

	print(query_url)
	response = requests.get(
		query_url
	)

	result = response.json()
	events = result["events"]

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
