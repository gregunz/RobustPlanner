// Leaflet initialization
let mymap = L.map('map_div').setView([47.378177, 8.540192], 12);

L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png', {
	attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
	subdomains: 'abcd',
	maxZoom: 19
}).addTo(mymap);
var OpenRailwayMap = L.tileLayer('https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png', {
	maxZoom: 19,
	attribution: 'Map data: &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> | Map style: &copy; <a href="https://www.OpenRailwayMap.org">OpenRailwayMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
}).addTo(mymap);

class city {
    constructor(name, lat, long) {
        this.name = name;
        this.lat = lat;
        this.long = long;
    }
  }

// let train_path_data;

// function loadTrainPath(CSV) {
//     train_path_data = CSV;
// }

// function getTrain_Path(trainline) {
//   train_path = train_path_data.filter(x => x.route_number == trainline)
//   return train_path.geoshape
// }

function draw_path(path) {
  let i = 0;
  clearMap(mymap);
  draw_marker(path[0]);
  while(i < path.length-1) {
    //draw_marker(path[i]);
    create_line(path[i], path[i+1]);
    i = i + 1;
  }
  draw_marker(path[path.length-1]);
  update_graph();
}

function draw_point(city) {
    var circle = L.circle([city.lat, city.long], {
        color: 'red',
        fillColor: '#f03',
        fillOpacity: 0.7,
        radius: 500,
    }).addTo(mymap);
}

function draw_marker(city) {
    let marker = L.marker([city.lat, city.long]);
    mymap.addLayer(marker);
    marker.bindPopup(city.name);
    myMarkers.push(marker);
}


let myLines = [];
let myMarkers = [];

function create_line(city1, city2) {
  myLines.push({
    'type': 'LineString',
    'coordinates': [[city1.long, city1.lat], [city2.long, city2.lat]]
  });
}

var myStyle = {
    "color": "#6555ed",
    "weight": 5,
    "opacity": 0.7
};

function clearMap(m) {
    myLines = [];
    for(i in m._layers) {
        if(m._layers[i]._path != undefined) {
            try {
                m.removeLayer(m._layers[i]);
            }
            catch(e) {
                console.log("problem with " + e + m._layers[i]);
            }
        }
    }

    myMarkers.forEach(function (m) {
        mymap.removeLayer(m);
    });
}


function update_graph() {
  L.geoJSON(myLines, {
      style: myStyle
  }).addTo(mymap);
}


// Ion Slider
$("#duration_slider").ionRangeSlider({
    grid: true,
    from: 3,
    values: [
        "5%", "10%", "15%", "20%",
        "25%", "30%", "35%", "40%",
        "45%", "50%", "55%", "60%",
        "65%", "70%", "75%", "80%",
        "85%", "90%", "95%", "100%"
    ]
});

// Form submission
$('#left_panel_form').on( "submit", function( event ) {
    console.log("charles fait super chier")
    showLoader(true)
    event.preventDefault();
    let params = $( this ).serialize();
    $.get('/api/v1.0/connections', params, function(json) {
        showLoader(false)
        console.log(json);
        if(json.code == 500) {
            alert("Server side error")
        } else {
            cities = json.city_path
            cities = cities.map(x => new city(x[0], x[1], x[2]))
            draw_path(cities);
        }
    });
});

function showLoader(show) {
    d3.select('#main_container').classed('blurdy', show)
    d3.select('#loader-overlay').style("visibility", show?"visible":"hidden");
}

city_names = []
const STOP_API_URL = '/api/v1.0/stops'
$.get(STOP_API_URL, function(json) {
    city_names = json.stops.sort()
    console.log(json)
    d3.selectAll('.city_select').selectAll('option').data(city_names).enter().append('option').text(function (d) { return d; });
})
