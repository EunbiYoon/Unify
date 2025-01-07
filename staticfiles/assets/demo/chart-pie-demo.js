// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#292b2c';

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: JSON.parse(PjinjaLabels),
    datasets: [{
      data: JSON.parse(PjinjaValues),
      backgroundColor: ['#36A2EB', '#FF6384', '#4BC0C0',  '#AE85FF','#FF9F40', '#FFCD56', '#C9CBCF', '#B3E5D1', '#B2C7E6', '#F5CFE7','#D3D0F4','#F3E5D1','#EFD5D5','#DCDCDC']
    }],
  },
  options:{
    legend:{
      position:'left'
    }
  }
});

