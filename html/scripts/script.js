
var createBarChart = function(ctx, data) {
        let delayed;
        let myChart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                maintainAspectRatio: false,
                animation: {
                    onComplete: () => {
                        delayed = true;
                    },
                    delay: (context) => {
                        let delay = 0;
                        if (context.type === 'data' && context.mode === 'default' && !delayed) {
                            delay = context.dataIndex * 80 + context.datasetIndex * 30;
                        }
                        return delay;
                    },
                },
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }});
        return myChart;
    }

var toggleStackedBtn = function(buttonName, chart) {
        button = document.getElementById(buttonName);
        if( button.value == "true" ) {
            button.value = "false";
            button.textContent = "Nebeneinander";
            button.classList.remove("m-btn-gray");
            button.classList.add("m-btn-orange");

            chart.options.scales.x.stacked = false;
            chart.options.scales.y.stacked = false;

        } else {
            button.value = "true";
            button.textContent = "Gestapelt";
            button.classList.remove("m-btn-orange");
            button.classList.add("m-btn-gray");

            chart.options.scales.x.stacked = true;
            chart.options.scales.y.stacked = true;
        }
        chart.update();
    };

var switchBtn = function(buttonName, messageName) {
        button = document.getElementById(buttonName);
        if( button.textContent == "EIN" ) {
            button.textContent = "AUS";
            button.style.color = "red";
            list = document.getElementsByName(messageName);
            for(i = 0; i < list.length; i++) {
                list[i].style.display = "none";
            }
        } else {
            button.textContent = "EIN";
            button.style.color = "green";
            list = document.getElementsByName(messageName);
            for(i = 0; i < list.length; i++) {
                list[i].style.display = "block";
            }
        }
    };

var monthsList = ["Januar", "Februar", "M\u00E4rz", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
var weekdaysList = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];