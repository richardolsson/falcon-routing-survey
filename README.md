Falcon routing survey
=====================

Survey and benchmarks of different routing strategies for a number of
real-life API designs. Conducted for the Falcon Python framework.

Background
----------
[Falcon](http://falconframework.org/) is a light framework for creating
RESTful API services, focusing on performance. One important target for
optimization is the URI routing performed by the framework for every
request.

Instead of naively benchmarking routing strategies against a fictional
set of URIs, the work in this repository is aimed towards surveying
real APIs and performing benchmarks for different routing strategies on
the URI schemes of those actual, live APIs.

The goal is to find the strategy which performs best under "real life
conditions" and to then go ahead and implement that in Falcon.

Surveyed APIs
-------------
The following APIs have (or will be) surveyed to create a catalog of 
different real-life API designs to test against. The available API
endpoint lists are available in the _apis_ folder.

* Facebook
* Twitter
* GitHub
* MailGun
* Mandrill
* Twilio
* Nexmo (two variants, see comments in .txt files)
* Spotify
* PayPal
* (more coming...)

Routing strategies
------------------
The code contains stand-alone implementations of two different routing
strategies.

The `RegexRouter` is an implementation of the same regex-based strategy
that is in use in Falcon today. It contains a map of compiled regular
expressions to responders, and the look-up is performed by iterating
over the expressions until a match is found or all have been tried.

The `TreeRouter` is an implementation of a possible replacement for the
O(n) regular expression based router. `TreeRouter` constructs a tree
representing the added routes at add time. Look-up is then performed
by splitting the URL and traversing the tree recursively.

The `CompiledTreeRouter` extends the `TreeRouter` but only uses the 
tree structure, while completely replacing the look-up code. Instead,
the `CompiledTreeRouter` generates Python code representing the route
tree completely inlined, compiles it and then executes it to find the
correct responder.

Usage
-----
Use the `benchmark.py` script to benchmark URL look-ups against the 
available router implementations.

### General usage:
```
    ./benchmark.py <api.txt> <url_to_find> [num_iterations]
```
The first two parameters are required. The default number of iterations
is 100.000. Timing is performed by the `timeit` module.

### Example:
Benchmark by searching for the `/repos/racker/falcon/issues/114/labels`
URL 200.000 times in the GitHub API.
```
    ./benchmark.py apis/github.txt /repos/racker/falcon/issues/114/labels 200000
```

`benchmark.py` first constructs the proper routers (and outputs some
debugging information while doing so) and then uses `timeit.timeit` to
time the look-up for all available routers.

### Output
Running the example above outputs something along these lines (ignoring
the initial debugging information):
```
----------------------------------------
BENCHMARKING ROUTER: tree_router
> from __main__ import tree_router
> tree_router.find_responder("/repos/racker/falcon/issues/114/labels")
RESULT: 3.99470496178s (200000 iterations)
RETURN: Resource(/repos/{owner}/{repo}/issues/{number}/labels)
----------------------------------------
BENCHMARKING ROUTER: regex_router
> from __main__ import regex_router
> regex_router.find_responder("/repos/racker/falcon/issues/114/labels")
RESULT: 8.51333618164s (200000 iterations)
RETURN: Resource(/repos/{owner}/{repo}/issues/{number}/labels)
----------------------------------------
BENCHMARKING ROUTER: compiled_router
> from __main__ import compiled_router
> compiled_router.find_responder("/repos/racker/falcon/issues/114/labels")
RESULT: 0.957674980164s (200000 iterations)
RETURN: Resource(/repos/{owner}/{repo}/issues/{number}/labels)
``` 

In this case, the tree router is roughly 2.2 times faster than the mock
implementation of the current Falcon regex router, and the Python code
generator router is another 4 times faster still.
