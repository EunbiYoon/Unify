const fetchAsync = async() => {
    const response = await fetch("../static/json/hazard.json"),
        keyValues = await response.json()
    return keyValues
}

fetchAsync().then(keyValues => {
    const time_labels = Object.values(keyValues.slice(1).map(element => element[0])),
        states = Object.values(keyValues[0]),
        covid_datasets = [],
        bc = [
            'rgb(27, 158, 119)', //green
            'rgb(35,70,169)',
            'rgb(166,38,75)',
            'rgb(217, 95, 2)', //orange
            'rgb(117, 112, 179)', //grape
            'rgb(231, 41, 138)', //pink
            'rgb(102, 166, 30)', //yellow green
            'rgb(230, 171, 2)', //yello
            'rgb(161,43,155)',
            'rgb(17,171,187)',
            'rgb(166, 118, 29)',//brown
            'rgb(102, 102, 102)'//grey
        ]
    for (let i = 1; i < states.length + 1; i++) {
        covid_datasets.push({
            label: states[i - 1],
            data: Object.values(keyValues.slice(1, states.length + 1).map(element => element[i])),
            backgroundColor: 'rgb(0,0,0,0)',
            borderColor: bc[states.length-i]
        })
    }
    const myNewChart = new Chart(document.getElementById('myTest'), {
        type: 'line',
        lineThickness: 1,
        data: {
            datasets: covid_datasets,
            labels: time_labels,
        },
        options: {
            elements: {
                point:{
                    radius: 0
                }
            },
            scales:{
                xAxes:[{   //remove gridLines from x-axis
                     gridLines:{
                        display:false
                     }
                    }],

               yAxes:[{    //remove gridLines from y-axis
                    gridLines:{
                        display:false
                      }
                    }]
            },
            legend:{
                position:'left'
            }
            
        },

    })
})
