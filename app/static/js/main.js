function getSong(song_id, multiplayer) {
    $.ajax({
        url: '/api/getSong/' + song_id,
        cache: false,
        dataType: 'json',
        success: multiplayer ? playMultiplayer : play,
    })
}

function play(data, sendCallback, winCallback) {
    var startTime = Date.now()
    $('.title').text(data.song.title)
    $('.collection').text(data.collection.title)
    $('.collection').attr('href', '/collection/' + data.collection._id.$oid)

    $('#back').text('View all songs in ' + data.collection.title)
    $('#back').attr('href', '/collection/' + data.collection._id.$oid)
    $('#random').text('Play another random song in ' + data.collection.title)
    $('#random').attr('href', '/random/' + data.collection._id.$oid)

    var lyrics = data.song.lyrics.split(' ').map(function (word) {
        return {
            simple: word.toLowerCase().replace(/[^\w]|_/g, ''),
            display: word,
            discovered: false,
        }
    })

    $('.total').text(lyrics.length)
    $('.complete').text(0)

    $('.lyricColumn').each(function () {
        for (var i = 0; i < Math.floor(lyrics.length / 5); i++) {
            $(this).append($('<div class="lyricBox covered"></div>'))
        }
    })

    for (var i = 0; i < lyrics.length % 5; i++) {
        $('.lyricColumn').eq(i).append($('<div class="lyricBox covered"></div>'))
    }

    $('#enter').keyup(function () {
        var word = $('#enter').val().toLowerCase().replace(/[^\w]|_/g, '')
        lyrics.forEach(function (lyric, index, arr) {
            if (lyric.simple === word && lyric.discovered === false) {
                $('#enter').val('')
                $('.lyricBox').eq(index).text(lyric.display)
                $('.lyricBox').eq(index).removeClass('covered')
                arr[index].discovered = true
                var complete = parseInt($('.complete').text()) + 1
                $('.complete').text(complete.toString())

                // sometimes it's a string saying 'success'
                if (typeof sendCallback === 'function') {
                    sendCallback(complete, lyrics.length)
                }

                if (complete === arr.length && $('.popup')[0].classList.contains('hidden')) {
                    var time = Date.now() - startTime
                    // if the callback exists, then hopefully the win screen will be
                    // created by the server
                    if (typeof winCallback !== 'function') {
                        createPopup(time)
                    } else {
                        winCallback(time)
                    }
                }
            }
        })
    })
}

function playMultiplayer(data) {
    var room = new URL(window.location.href).pathname.slice(6)
    var socket = io();

    socket.on('connect', function () {
        console.log('Connected')
        socket.emit('join', { room });
        var numerator = parseInt($('.complete').text())
        var denominator = data.song.lyrics.split(' ').length
        socket.emit('send update', { numerator, denominator, room })
    });

    socket.on('members', function (data) {
        $('.members').empty()
        data.members.forEach(function (member) {
            var percentage = (member.denominator === 0 ? 0 : Math.floor((member.numerator / member.denominator) * 100))
            $('.members').append(`<div class="member" id="${member.id}">${member.username} ${percentage}%</div>`)
        })
    })

    socket.on('update', function (data) {
        const { id, username, numerator, denominator } = data
        var percentage = (denominator === 0 ? 0 : Math.floor((numerator / denominator) * 100))
        $(`#${id}`).text(`${username} ${percentage}%`)
    })

    socket.on('victory', function (data) {
        createPopup(data["time"], data["winner"])
        socket.disconnect()
    })

    // play, with callbacks to send completed words
    play(data, function (numerator, denominator) {
        socket.emit('send update', { numerator, denominator, room })
    }, function (time) {
        socket.emit('client won', { time, room })
        return true
    })
}

function createPopup(time, winner = 'You') {
    var minutes = Math.floor(time / 60000)
    var seconds = Math.floor(time / 1000) % 60
    $('.popupText').text(`${winner} completed this song in ${minutes}m ${seconds}s`)
    $('.popup').removeClass('hidden')
}

$(document).ready(function () {
    $('.collection').click(() => {
        $(this).toggleClass('expanded')
    })
})