// Global parameters:
// do not resize the chart canvas when its container does (keep at 600x400px)
// Chart.defaults.global.responsive = false;
// define the chart data
var chartData = {
  labels: JSON.parse(jinjaLabels),
  
  datasets: [{
    data: JSON.parse(Bjinja2MValues),
    label: jinja2MLegend,
    backgroundColor: "#c2c0c0",
    pointHoverRadius: 5,
    pointHoverBackgroundColor: "#164F63",
    pointRadius: 1,
    pointHitRadius: 10
    },
    {
      data: JSON.parse(Bjinja1MValues),
      label: jinja1MLegend,
      backgroundColor: "#8bc7f0",
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "#164F63",
      pointRadius: 1,
      pointHitRadius: 10
    },
    {
      data: JSON.parse(Bjinja0MValues),
      label: jinja0MLegend,
      backgroundColor: "#ff9eb2",
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "#164F63",
      pointRadius: 1,
      pointHitRadius: 10
    }

  ]
};

console.log(jinjaLabels);
console.log(Bjinja2MValues);
console.log(Bjinja1MValues);
console.log(Bjinja0MValues);



// get chart canvas
var ctx = document.getElementById("barchart").getContext("2d");

// create the chart using the chart canvas
var barchart = new Chart(ctx, {
  type: 'bar',
  data: chartData,
});
