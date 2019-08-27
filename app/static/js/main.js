function getSong(song_id, multiplayer) {
    $.ajax({
        url: '/api/getSong/' + song_id,
        cache: false,
        dataType: 'json',
        success: multiplayer ? playMultiplayer : play,
    })
}

function play(data, sendCallback = function () { }, winCallback = function () { }) {
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
        console.log(word)
        lyrics.forEach(function (lyric, index, arr) {
            if (lyric.simple === word && lyric.discovered === false) {
                $('#enter').val('')
                $('.lyricBox').eq(index).text(lyric.display)
                $('.lyricBox').eq(index).removeClass('covered')
                arr[index].discovered = true
                var complete = parseInt($('.complete').text()) + 1
                $('.complete').text(complete.toString())
                sendCallback(complete, lyrics.length)
                if (complete === arr.length && $('.popup').classList.contains('hidden')) {
                    var time = Date.now() - startTime
                    // if the callback exists, then hopefully the win screen will be
                    // created by the server
                    var callbackExists = winCallback(time)
                    if (!callbackExists) {
                        createPopup(time)
                    }
                }
            }
        })
    })
}

function playMultiplayer(data, room) {
    var socket = io();
    socket.on('connect', function () {
        socket.emit('join', { data: { room } });
    });
    socket.on('members', function (data) {
        $('.members').empty()
        data.members.forEach(function (member) {
            $('.members').append(`<div class="member" id="${member._id}">${member.username} ${Math.floor(member.numerator / member.denominator)}%</div>`)
        })
    })
    socket.on('update', function (data) {
        const { _id, username, numerator, denominator } = data
        $(`#${_id}`).innerText(`${username} ${Math.floor(numerator / denominator)}%`)
    })
    socket.on('victory', function (data) {
        createPopup(data.time, data.winner)
    })
    // play, with a callback to send completed words
    play(data, function (numerator, denominator) {
        socket.emit('update', { data: { numerator, denominator } })
    }, function (time) {
        socket.emit('victory', { data: { time } })
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