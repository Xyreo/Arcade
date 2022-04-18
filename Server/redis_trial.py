import redis, time, json

start = time.perf_counter()
r = redis.Redis(host="localhost", port=6379, db=0)
serialize = r.get("monopoly_board_values")
get = time.perf_counter()
prop = json.loads(serialize)
deserialize = time.perf_counter()
prop[1] = None
prop = json.dumps(prop)
serialize = time.perf_counter()


print(get - start)
print(deserialize - get)
print(serialize - deserialize)
