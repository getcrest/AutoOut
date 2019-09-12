$(document).ready(function () {
    var page_no = 1;
    var outlierArray = [];
    var experiment_id;
    var datasetID;
    var uppy = Uppy.Core({
        autoProceed: true,
        restrictions: {
            maxFileSize: 1000000000,
            maxNumberOfFiles: 1,
            minNumberOfFiles: 1,
            allowedFileTypes: ['text/csv', 'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/x-hdf']
        }
    });
    uppy.use(Uppy.Dashboard, {
        target: '#drag-drop-area', inline: true,
        note: 'CSV, HDF and Excel files only. We support tabular data only!',
        height: 200,
        width: 500
    });
    uppy.use(Uppy.XHRUpload, {endpoint: 'file/upload'});

    uppy.on('complete', (result) => {
        console.log('Upload complete! We’ve uploaded these files:', result);

        $("#dataset_block").fadeOut(300);
        $("#data-table-view").hide().fadeIn(300);
        $("#tableNavigator").hide().fadeIn(300);

        datasetID = result.successful[0].response.body.dataset_id;
        getDatasetProperties();
        getAndPopulateData();
    });

    function get_datasets() {
        $.ajax({
            url: `/app/datasets`,
            success: function (result) {
                console.log(result);
                // Populate datasets

                dataset_list = $("#dataset-list");
                for (i = 0; i < result.length; i++) {
                    dataset_list.append("<li class='list-group-item' data-dataset-id=" + result[i].id + ">" + result[i].id + "-" + result[i].name + "</li>")
                }
            },
            failure: function (result) {
                alert("Failed to fetch datasets")
            }
        })
    }

    get_datasets();

    function getDatasetProperties() {
        $.ajax({
            url: `/app/data/properties?dataset_id=${datasetID}`,
            success: function (result) {
                $(".datasetInfo").hide().fadeIn(300);
                console.log(result);
                $("#categoricalFeatures").text(result.no_categorical_features);
                $("#totalFeatures").text(result.no_features);
                $("#numericalFeatures").text(result.no_numerical_features);
                $("#totalSamples").text(result.no_samples);
                $("#detectedOutliers").text(result.detected_outliers);
            },
            failure: function (result) {
                alert("Failed to fetch dataset properties")
            }
        })
    }

    function getAndPopulateData() {
        $.ajax({
            url: `/app/data/get?dataset_id=${datasetID}`, success: function (result) {
                let dataTableView = $("#data-table-view");
                let results = JSON.parse(result);
                console.log(results[0]);

                // Fill column names
                let headHtml = $("<tr>");
                let keys = Object.keys(results[0]);
                for (let i = 0; i < keys.length; i++) {
                    headHtml.append("<th>" + keys[i] + "</th>");
                }
                headHtml.append("</tr>");
                dataTableView.find("thead").append(headHtml);

                // Fill values
                for (let i = 0; i < results.length; i++) {
                    let result1 = results[i];
                    let rowHtml = $("<tr>");
                    for (let j = 0; j < keys.length; j++) {
                        //console.log(result1[keys[j]]);
                        rowHtml.append($("<td>" + result1[keys[j]] + "</td>"));
                    }
                    rowHtml.append($("</tr>"));
                    dataTableView.find("tbody").append(rowHtml);
                }
                $("#detectButton").show();
            }
        });
    }

    $("#detectButton").click(() => {
        $("#detectButton").hide();
        $("#loadingButton").show();
        $("#loadingText").text("Detecting");
        $.ajax({
            url: `/app/outliers/detect?dataset_id=${datasetID}`, success: function (result) {
                console.log("RESULTS");
                console.log(result);
                experiment_id = result.experiment_id;
                var pollId = setInterval(() => {
                    $.ajax({
                        url: "/app/status/get",
                        method: "POST",
                        data: JSON.stringify({
                            "experiment_id": experiment_id
                        }),
                        success: function (result) {
                            console.log(result);
                            getDatasetProperties();
                            if (result.experiment_status === "Completed") {
                                clearInterval(pollId);
                                $("#loadingButton").hide();
                                $("#treatButton").show();

                                // Colorize detected rows
                                $.ajax({
                                        url: "/app/outliers/get",
                                        method: "POST",
                                        data: JSON.stringify({
                                            "experiment_id": experiment_id
                                        }),
                                        success: function (result) {
                                            console.log(result);

                                            var outliers = result['outliers'];
                                            outlierArray = outliers;

                                            let totalOutliers = 0;
                                            if (outlierArray !== undefined) {
                                                totalOutliers = outlierArray.length;
                                            }
                                            $("#detectedOutliers").text(totalOutliers);
                                            fillTable(1);
                                        },
                                        failure: function (result) {
                                            $("#loadingButton").hide();
                                        }
                                    }
                                )
                            }
                        },
                        failure: function (result) {
                            $("#loadingButton").hide();
                        }
                    })
                }, 5000);
            },
            failure: function (result) {
                console.log("Failed to detect outliers");
                $("#loadingButton").hide();
                alert("Failed to detect outliers");
            }
        });
    });

    $("#treatButton").click(() => {
        $("#selectTreatPercentageModal").modal("show");
    });

    $("#treatButton2").click(() => {
        console.log("Clicked");
        let option = $("#selectTreatPercentageModal input:radio:checked").val();
        let treatPercentage = 100;

        if (option === "option2") {
            treatPercentage = $("#treatPercentage").val();
            if (treatPercentage === "") {
                return;
            } else {
                treatPercentage = parseInt(treatPercentage)
            }
        } else if (option === "option1") {
            treatPercentage = 100;
        }

        console.log("Treat percentage:", treatPercentage);

        $("#loadingButton").show();
        $("#loadingText").text("Treating");
        $("#treatButton").hide();

        $.ajax({
            url: '/app/outliers/treat?',
            method: 'POST',
            data: JSON.stringify({
                experiment_id: experiment_id,
                treat_percentage: treatPercentage
            }),
            contentType: "application/json",
            success: function (result) {
                console.log("Treat Results");
                console.log(result.experiment_id);

                if(result.status === "success"){
                    $("#selectTreatPercentageModal").modal("hide");
                }else{
                    alert("Error:"+result);
                    return;
                }

                let treatment_expr_id = result.experiment_id;
                var pollId = setInterval(() => {
                    $.ajax({
                        url: "/app/status/get",
                        method: "POST",
                        data: JSON.stringify({
                            "experiment_id": experiment_id
                        }),
                        success: function (result) {
                            console.log(result);
                            if (result.experiment_status === "Completed") {
                                clearInterval(pollId);
                                $("#loadingButton").hide();
                                //$("#treatButton").show();
                                $("#downloadButton").show();
                                $("#downloadButton").attr("href", `/app/file/download?experiment_id=${treatment_expr_id}`)
                            }
                        },
                        failure: function (result) {
                            $("#loadingButton").hide();
                        }
                    })
                }, 5000);
            },
            failure: function (result) {
                console.log("Failed to treat outliers");
                $("#loadingButton").hide();
                alert("Failed to treat outliers");
            }
        })
    });

    function nextPage() {
        page_no++;
        fillTable(page_no);
    }

    function previousPage() {
        if (page_no > 1) {
            page_no--;
            fillTable(page_no);
        }
    }

    function fillTable(page_num) {
        $.ajax({
            url: `/app/data/get?page_num=${page_num}&dataset_id=${datasetID}`, success: function (result) {
                let dataTableView = $("#data-table-view");
                let results = JSON.parse(result);
                console.log(results[0]);

                // Fill column names
                let headHtml = $("<tr>");
                let keys = Object.keys(results[0]);
                for (let i = 0; i < keys.length; i++) {
                    headHtml.append("<th>" + keys[i] + "</th>");
                }
                headHtml.append("</tr>");
                dataTableView.find("thead").html(headHtml);

                // Fill values
                dataTableView.find("tbody").html('');
                for (let i = 0; i < results.length; i++) {
                    let result1 = results[i];
                    let rowHtml;

                    if (outlierArray === undefined) {
                        outlierArray = [];
                    }
                    if (outlierArray.includes((page_num - 1) * 20 + i)) {
                        console.log("Row Number");
                        console.log((page_num - 1) * 20 + i);
                        rowHtml = $("<tr style='background-color:#ff3c41; color:white'>");
                    } else {
                        rowHtml = $("<tr>");
                    }
                    for (let j = 0; j < keys.length; j++) {
                        //console.log(result1[keys[j]]);
                        rowHtml.append($("<td>" + result1[keys[j]] + "</td>"));
                    }
                    rowHtml.append($("</tr>"));
                    dataTableView.find("tbody").append(rowHtml);

                }
                //$("#detectButton").show();
            }
        });
    }

    $('body').on('click', '#dataset-list li', function () {
        console.log($(this).text());

        $("#dataset_block").fadeOut(300);
        $("#data-table-view").hide().fadeIn(300);
        $("#tableNavigator").hide().fadeIn(300);

        datasetID = $(this).data("dataset-id");
        getDatasetProperties();
        getAndPopulateData();
    });
});
