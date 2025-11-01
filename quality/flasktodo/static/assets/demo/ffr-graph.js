// Global parameters:
// do not resize the chart canvas when its container does (keep at 600x400px)
// Chart.defaults.global.responsive = false;
// define the chart data
var chartData = {
  labels: JSON.parse(FFRLabels),
  
  datasets: [
    {
      data: JSON.parse(FFR1YValues),
      label: FFR1YLegend,
      // borderColor:'#2A4C4C',
      borderColor:'#2A4C4C',
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "green",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FFR2YValues),
      label: FFR2YLegend,
      borderColor:"#539999",
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FFR3YValues),
      label: FFR3YLegend,
      borderColor:"#B8E6E6",
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FFR4YValues),
      label: FFR4YLegend,
      borderColor:'#e9f7f7',
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FDR1YValues),
      label: FDR1YLegend,
      fill:false,
      borderColor:"#5b4266",
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "purple",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FDR2YValues),
      label: FDR2YLegend,
      borderColor:"#c6abd0",
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    },
    {
      data: JSON.parse(FDR3YValues),
      label: FDR3YLegend,
      borderColor:"#f4d8ff",
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,      
      pointRadius:3
    },
    {
      data: JSON.parse(FDR4YValues),
      label: FDR4YLegend,
      borderColor:"#fbf1ff",
      fill:false,
      pointHoverRadius: 3,
      pointHoverBackgroundColor: "grey",
      pointRadius: 1,
      pointHitRadius: 10,
      pointRadius:3
    }   
  ]
};


// get chart canvas
var ctx = document.getElementById("ffrchart").getContext("2d");

// create the chart using the chart canvas
var areachart = new Chart(ctx, {
  type: 'line',
  data: chartData,
  options: {
    scales: {
      xAxes: [{
        type: 'category',
        gridLines:{
          display:false
        }
      }],
      yAxes: [{
        gridLines:{
          display:false
        }
      }]
    },
    legend:{
      position:'right'
    }
  },
  animation: {
    onComplete: function () {
      var chartInstance = this.chart;
      var ctx = chartInstance.ctx;
      ctx.textAlign = "center";
      ctx.font = "20px Arial";
      ctx.fillStyle = "white";                            
      Chart.helpers.each(this.data.datasets.forEach(function (dataset, i) {
        var meta = chartInstance.controller.getDatasetMeta(i);
        Chart.helpers.each(meta.data.forEach(function (bar, index) {
          if (chartInstance.data.datasets[i].data[index] !== 0) {
            ctx.save();
            ctx.translate(bar._model.x - 10, bar._model.y - 19);
            ctx.rotate(-0.5 * Math.PI);
            ctx.fillText(dataset.data[index], 0, 0);
            ctx.restore();
          }
        }),this)
      }),this);
    }
  }
  
});
