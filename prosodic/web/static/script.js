
function getCurrentDateTime() {
    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0'); // getMonth() returns 0-11
    const day = String(now.getDate()).padStart(2, '0');

    const hour = String(now.getHours()).padStart(2, '0');
    const minute = String(now.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}-${hour}${minute}`;
}



function get_table() {
    var export_cols = [0, 1, 2, 3, 5, 6, 7, 8, 9, 10];
    for (i in all_constraints) {
        export_cols.push(i+11);
    }

    var export_opts = {
        columns: export_cols
    }

    var columnDefs = [];
    var invis_cols = new Set([2,5,6,7]);
    for (i of [...Array(11 + all_constraints.length).keys()]) {
        if(i==4) { width='30em'; } else { width='50px'; }
        columnDefs.push({
            'width':width,
            'targets':i,
            'visible':!invis_cols.has(i)
        })
    }
    console.log('columnDefs',columnDefs);

    var buttons = [];
    var ext2header = {
        'copy':true,
        'csv':true,
        'excel':true,
        'pdf':true,
        'print':true,
    }

    for (ext in ext2header) {
        d = {
            header:ext2header[ext],
            extend: ext,
            footer:false,
            exportOptions:export_opts,
            title:'prosodic_export_' + getCurrentDateTime()
        }
        buttons.push(d);
    }

    var table = $('#table_lines').DataTable({
        dom: 'Bfrtip',
        buttons:buttons,
        fixedHeader: true,
        scrollX: true,
        bScrollInfinite: true,
        bScrollCollapse: true,
        sScrollY: "82.5vh",
        pageLength: 100,
        order: [[0, "asc"], [1, "asc"], [3, "asc"]],
        columnDefs: columnDefs
    });

    return table;
}

function get_progbar() {
    var bar = new ProgressBar.Line('#progressbar', {
        color: 'rgba(202, 202, 202, .6)',
        // strokeWidth: 1,
        // duration: 0,
    });

    bar.setText('');
    bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
    bar.text.style.fontSize = '.9rem';
    bar.text.style.margin = '0 auto';
    bar.text.style.color = 'rgba(0,0,0,0.5)';

    return bar;
}

function get_progbar2() {
    pjs=progressJs().setOptions({'theme': 'black', 'overlayMode': true }).start();
    return pjs;
}







// A $( document ).ready() block.
$(document).ready(function () {
    // GLOBAL VARS
    var table = get_table();
    // var bar = get_progbar();
    var socket = io();

    function submit() {
        data = $('#inputform').serializeArray();
        // bar.set(50);
        // bar.setText('parsing...');
        // $('#progressbar').fadeIn('fast');
        // $('#progressbar').text('');
        if (data) {
            ojson = JSON.stringify(data);
            socket.emit('parse', ojson);
        }
    }

    // socket.on('connect', function () {
        socket.on('parse_result', function (event_data) {
            data = JSON.parse(event_data);
            rownum = data.rownum;
            // bar.animate(data.progress);
            // bar.set(data.progress * 100);
            // table.row.add(data.row).draw();
            row = table.row(rownum);
            rowdat = row.data();
            if (!rowdat) {
                table.row.add(data.row).draw();
            } else {
                row.data(data.row).draw();
            }

            if (data.progress != 1) {
                remaining = Math.round(data.remaining);
                if (remaining == 0) { remaining = '<1' } else { remaining = remaining.toString(); }
                progress = Math.round(data.progress * 100);
                msg = progress.toString() + '% complete, eta: ' + remaining + 's';
                // bar.setText(msg);
                $('#parsebtn').text(msg);
            } else {
                let pbtn = $('#parsebtn');
                pbtn.html('Parse');
                pbtn.prop("disabled", false);
                // let pbar = $('#progressbar');

                numdone = rownum+1;
                numintbl = table.rows().count()+1;  
                if (numintbl - numdone > 0) {
                    todel=[];
                    for (xi = numdone; xi < numintbl; xi++) {
                        todel.push(xi);
                    }
                    table.rows(todel).remove().draw()
                }

                // setTimeout(function () {
                // bar.setText('');
                // pbar.fadeOut('slow');
            }


        });


    // });

    $('#parsebtn').on('click', function () {
        // $('#progressbar').show();
        let pbtn = $('#parsebtn');
        pbtn.html('Parsing...');
        pbtn.prop("disabled", true);
        submit();
    });
    
    setTimeout(function () { $('#parsebtn').click(); }, 500);
});