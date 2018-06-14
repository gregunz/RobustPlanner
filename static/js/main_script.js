// Leaflet initialization
let mymap = L.map('map_div').setView([47.378177, 8.540192], 12);

L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}{r}.{ext}', {
    attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    subdomains: 'abcd',
    minZoom: 0,
    maxZoom: 20,
    ext: 'png'
}).addTo(mymap);
// var OpenRailwayMap = L.tileLayer('https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png', {
// 	maxZoom: 19,
// 	attribution: 'Map data: &copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> | Map style: &copy; <a href="https://www.OpenRailwayMap.org">OpenRailwayMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
// }).addTo(mymap);
L.control.scale().addTo(mymap)

class city {
    constructor(name, lat, long) {
        this.name = name;
        this.lat = lat;
        this.long = long;
    }
}
class Connection {
    constructor(from_city, to_city, departure_time, arrival_time, trip_id, proba, proba_cumul) {
        this.from_city = from_city;
        this.to_city = to_city;
        this.departure_time = departure_time;
        this.arrival_time = arrival_time;
        this.proba = proba;
        this.proba_cumul = proba_cumul;
        this.trip_id = trip_id;
    }
}

class Trip {
    constructor(connections, duration, name) {
        this.connections = connections
        this.duration = duration
        this.name = name
    }
}


function draw_trip(trip) {
    path = trip.connections
    let i = 0;
    clearMap(mymap);
    draw_marker(path[0].from_city, "");
    while(i < path.length) {
        //draw_marker(path[i]);
        create_line(path[i]);
        i = i + 1;
    }
    draw_marker(path[path.length-1].to_city, path[path.length-1].arrival_time);
    update_graph();

    //center the map
    allStation = [[path[0].from_city.lat, path[0].from_city.long]]
    allStation = allStation.concat(path.map(x=> [x.to_city.lat, x.to_city.long]))
    mymap.fitBounds(allStation);
}

function draw_point(city) {
    var circle = L.circle([city.lat, city.long], {
        color: 'red',
        fillColor: '#f03',
        fillOpacity: 0.7,
        radius: 500,
    }).addTo(mymap);
}

function draw_marker(city, text) {
    let marker = L.marker([city.lat, city.long]);
    mymap.addLayer(marker);
    marker.bindPopup(city.name + '<br>' + text);
    myMarkers.push(marker);
}


let myLines = [];
let myMarkers = [];

function create_line(connection) {
    city1 = connection.from_city
    city2 = connection.to_city
    myLines.push({
        'type': 'LineString',
        'coordinates': [[city1.long, city1.lat], [city2.long, city2.lat]],
        'proba': connection.proba,//proba_cumul,
        'trip_id': connection.trip_id
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
        style: function (line) {
            prob = line.geometry.proba//Math.random()
            if(line.geometry.trip_id == 'Walk'){
                myStyle.dashArray = '5, 5'
                myStyle.color = '#000000'
            } else {
                myStyle.dashArray = ''
                myStyle.color = d3.interpolateRdYlGn(prob)//"#55ed65"
            }
            return myStyle
        }
    }).addTo(mymap);
}


// Ion Slider
$("#duration_slider").ionRangeSlider({
    grid: true,
    from: 14,
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
    showLoader(true);
    event.preventDefault();
    let params = $( this ).serialize();
    $.get('/api/v1.0/connections', params, function(json) {
        showLoader(false)
        if(json.code == 500) {
            swal ( "Oops" ,  "No connections found :( !" ,  "error" )
        } else {
            console.log(json);
            allTrips = json.trips.map(trip => new Trip(
                trip[0].map(x => new Connection(new city(...x[0]),
                new city(...x[1]),
                x[2], x[3], x[4], x[5], x[6])), trip[1], trip[2])
        )
            Vue.set(tripList,'trips', allTrips);
            //console.log(connections)
            draw_trip(allTrips[0]);
        }
    });
});

function showLoader(show) {
    d3.select('#main_container').classed('blurdy', show);
    d3.select('#loader-overlay').style("visibility", show?"visible":"hidden");
}

city_names = [];
const STOP_API_URL = '/api/v1.0/stops';
$.get(STOP_API_URL, function(json) {
    city_names = json.stops.sort();
    //d3.selectAll('.city_select').selectAll('option').data(city_names).enter().append('option').text(function (d) { return d; });
    d3.select('#departure').selectAll('option').data(city_names).enter().append('option').text(function (d) { return d; }).property("selected", function(d){ return d === 'Zürich Flughafen, Bahnhof'; })
    d3.select('#arrival').selectAll('option').data(city_names).enter().append('option').text(function (d) { return d; }).property("selected", function(d){ return d === 'Zürich, ETH/Universitätsspital'; })
});


//legends
var legend = L.control({position: 'bottomright'});

legend.onAdd = function (map) {

    var div = L.DomUtil.create('div', 'info legend'),
        grades = [0, 20, 40, 60, 80, 100],
        labels = [];

    // loop through our density intervals and generate a label with a colored square for each interval
    div.innerHTML += "<div>Certainty:</div>";
    for (var i = 0; i < grades.length-1; i++) {
        div.innerHTML +=
            '<div style="display: inline-block"><i style="background:' + d3.interpolateRdYlGn((grades[i] + grades[i + 1])/200) + '"></i> ' +
            grades[i] + '&ndash;' + grades[i + 1]  + '%</div><br>';
    }
    div.innerHTML +=
        '<div style="display: inline-block"><i style="background: black"></i> walking</div><br>';

    return div;
};

legend.addTo(mymap);

//defautl values
d = new Date();
document.getElementById("start_date").valueAsDate = d;
document.getElementById("start_time").value = d.getHours() + (d.getMinutes()<10?":0":":") + d.getMinutes()


//VueJs
var tripList = new Vue({
    el: '#trips',
    data: {
        trips: [],
        selectedIndex: 0
    },
    methods: {
        show: function(index, trip) {
            this.selectedIndex = index;
            draw_trip(trip)
        }
    }
});

function buy_tickets(){
    const form_data = $('#left_panel_form').serializeArray();
    const from = form_data[0].value;
    const to = form_data[1].value;
    var date = form_data[2].value.split('-');
    date = date[2] + "." + date[1] + "." + date[0];
    var time = form_data[3].value.split(':');
    time = time[0] + "%3A" + time[1];
    var link = "https://www.sbb.ch/fr/acheter/pages/fahrplan/fahrplan.xhtml?suche=true" +
        "&von=" + from + "&nach=" + to + "&datum=" + date + "&zeit=" + time;
    //link = encodeURI(link);
    window.open(link, '_blank');
}
