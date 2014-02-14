
			var width = 700,
			    height = 400;
			
			var color = d3.scale.category20();
			
			var force = d3.layout.force()
			    .charge(-120)
			    .linkDistance(70)
			    .size([width, height]);
			
			var svg = d3.select(".graph").append("svg")
			    .attr("width", width)
			    .attr("height", height);
			
			d3.json("get_song_graph_json", function(error, graph) {
			  force
			      .nodes(graph.nodes)
			      .links(graph.links)
			      .start();
			
			  var link = svg.selectAll(".link")
			      .data(graph.links)
			    .enter().append("line")
			      .attr("class", "link")
			      .style("stroke-width", function(d) { return Math.sqrt(d.value); });
			
			  var node = svg.selectAll(".node")
			      .data(graph.nodes)
			    .enter() .append('g');
			    
			    
			    
			    node.append("circle")
			      .attr("class", "node")
			      .attr("r", 5)
			      .style("fill", function(d) { return color(/*d.group*/1); })
			      .call(force.drag);
			
			  node.append("title")
			      .text(function(d) { return d.name; });
			      
			  var labels = node.append("text")
  				.text(function(d) { /*return d.name; */});

							
			  force.on("tick", function() {
			    link.attr("x1", function(d) { return d.source.x; })
			        .attr("y1", function(d) { return d.source.y; })
			        .attr("x2", function(d) { return d.target.x; })
			        .attr("y2", function(d) { return d.target.y; });
			
			    node.attr("cx", function(d) { return d.x; })
			        .attr("cy", function(d) { return d.y; });
			        
						  // Translate the groups
									  node.attr("transform", function(d) { 
										return 'translate(' + [d.x, d.y] + ')'; 
										  });  
			  });
});