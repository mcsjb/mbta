## Implemention notes on questions:
### Question one:
Straightforward API call to get all routes.  
Used the built in filter type from the API because all the questions only deal with subway routes.  
There was no need to fetch and process the additional information on the client side.

### Question two:
Spent some amount of time here figuring out an efficient way to associate stops with routes.  
The stops endpoint will take routes as a filter, but does not return the stop to route relationship on return.  
I attempted various stop end point options like including relationships, but could not get the data I was looking for.  
Next I tried the trips endpoint, which I could call with all the routes, and it would return a list of stops per route, so that was a single API call for the data I was looking for, but stops returned in trips were not exaclty what I was looking for and would have needed more calls and mappings.  
So I settled on one call into /stops per route.  This felt ineffecient but I could not find a better option in the API.

Only other thing of note is there is a tie for most stops on a route.

### Question three:
This is a path solving problem, but in the spirit of the question I intentionally did not look up any algoritim solutions.
The first step in solving this was taking the map of routes->stops built in question two, and inverting it so we had a map of stops->routes.  
Using that map, build a graph where each stop is a node and the edges are the routes the connect the nodes.

From there I did not apply any specific path weighting or priority, 
only choosing not to switch lines if there is more then one edge on a stop, and you are currently on one of the edge(route)
So it was a brute force approach of walking each node\edge until the given final stop is found.

As mentioned, did not attempt to apply known path finding algorithims.  
But even before applying any algorithms, the starting graph should be much more efficient then the way I built it.
As noted in some of the code comments:  

There are simply too many nodes in the graph.
One option would be to only use stops that connect routes as nodes.  
There is no need to traverse nodes that only connect to the next stop in the line with no transfer options, it is wasted cycles.
Possibly only connecting a stop to its next stop on the same line.  The way it is now, each stop is connected to every other stop on the line, which is also wasted cycles.


A different option would be to make the routes the nodes, and the edges the connecting stops. One each route we could then check if destination stop was available.
This would reduce size of graph, needing less traversal.  Since the question only required mentioned changing stops\lines.

Would have to profile\look at options, I think either would be an improvement.