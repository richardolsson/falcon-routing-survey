Falcon routing survey
=====================

Survey and benchmarks of different routing strategies for a number of
real-life API designs. Conducted for the Falcon Python framework.

Surveyed APIs
-------------
The following APIs have (or will be) surveyed to create a catalog of 
different real-life API designs to test against. The available API
endpoint lists are available in the _apis_ folder.

* Facebook
* Twitter
* GitHub
* (more coming...)

Routing strategies
------------------
The code contains standa-lone implementations of two different routing
strategies.

The `RegexRouter` is an implementation of the same regex-based strategy
that is in use in Falcon today. It contains a map of compiled regular
expressions to responders, and the look-up is performed by iterating
over the expressions until a match is found or all have been tried.

The `TreeRouter` is an implementation of a possible replacement for the
O(n) regular expression based router. `TreeRouter` constructs a tree
representing the added routes at add time. Look-up is then performed
by splitting the URL and traversing the tree recursively.

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
-----------
BENCHMARKING ROUTER: tree_router
> from __main__ import tree_router
> tree_router.find_responder("/repos/racker/falcon/issues/114/labels")
RESULT: 3.87302017212s (200000 iterations)
RETURN: Resource(/repos/{owner}/{repo}/issues/{number}/labels)
-----------
BENCHMARKING ROUTER: regex_router
> from __main__ import regex_router
> regex_router.find_responder("/repos/racker/falcon/issues/114/labels")
RESULT: 8.60835313797s (200000 iterations)
RETURN: Resource(/repos/{owner}/{repo}/issues/{number}/labels)
``` 

In this case, the tree router is roughly 2.2 times faster than the mock
implementation of the current Falcon regex router.