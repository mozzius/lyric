function getSong(song_id, multiplayer, random) {
    $.ajax({
        url: '/api/getSong/' + song_id,
        indexValues: { random: !!random },
        dataType: 'json',
        success: multiplayer ? playMultiplayer : play,
    })
}

function play(data, rand, sendCallback, winCallback) {
    var startTime = Date.now()
    $('.title').text(data.song.title)
    $('.collection').text(data.collection.title)

    const random = (typeof rand === 'boolean' ? rand : this.indexValues.random)
    const song_id = data.song._id.$oid
    const song_title = data.song.title
    const collection_id = data.collection._id.$oid
    const collection_title = data.collection.title

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

                if (complete === arr.length && $('.popup').hasClass('hidden')) {
                    var time = Date.now() - startTime
                    // if the callback exists, then hopefully the win screen will be
                    // created by the server
                    if (typeof winCallback !== 'function') {
                        createPopup('singleplayer complete', { time, random, collection_id, collection_title, song_id, song_title })
                    } else {
                        winCallback(time)
                    }
                }
            }
        })
    })
}

function playMultiplayer(data) {
    const room = new URL(window.location.href).pathname.slice(6)
    const socket = io(location.protocol + "//" + document.domain + ":" + location.port + "/multiplayer");

    const song_title = data.song.title
    const collection_title = data.collection.title
    const random = this.indexValues.random

    socket.on('connect', function () {
        console.log('Connected')
        socket.emit('join', { room });
        var numerator = parseInt($('.complete').text())
        var denominator = data.song.lyrics.split(' ').length
        socket.emit('word found', { numerator, denominator, room })
    });

    socket.on('start', function () {
        // play, with callbacks to send completed words
        play(data, random, function (numerator, denominator) {
            socket.emit('word found', { numerator, denominator, room })
        }, function (time) {
            socket.emit('client won', { time, room })
            return true
        })
        closePopup()
    })

    socket.on('members', function (data) {
        // .sort(function (a, b) { return b.numerator - a.numerator })
        console.log(`started: ${data.started}`)
        if (!data.started) {
            can_start = data.user_id == id
            createPopup('multiplayer start', {
                random, song_title, collection_title, can_start, clickFunc: function () {
                    socket.emit('please start', { room })
                }
            })
        }
        displayMembers(data.members, data.started)
    })

    socket.on('update', function (data) {
        const { id, username, numerator, denominator, started } = data
        var percentage = (denominator === 0 ? 0 : Math.floor((numerator / denominator) * 100))
        $(`#${id}`).text(`${username}${started ? ` ${percentage}%` : ''}`)

        function getPercentage(element) {
            return parseInt($(element).text().split(' ').pop().slice(0, -1))
        }
        $('.member').sort(function (a, b) { return getPercentage(b) - getPercentage(a) })
    })

    socket.on('victory', function (data) {
        createPopup('multiplayer complete', { time: data["time"], random: random, song_title, winner: data["winner"] })
        displayMembers(data.members, true)
        socket.disconnect()
    })

    socket.on('disconnect', function () {
        console.log('Disconnected')
        if ($('.popup').hasClass('hidden')) {
            createPopup('disconnected')
        }
    })
}

function createPopup(type, data) {
    closePopup()
    var box = $('<div>').addClass('box')

    if (type === 'singleplayer complete') {
        const { time, random, song_id, song_title, collection_id, collection_title } = data
        var minutes = Math.floor(time / 60000)
        var seconds = Math.floor(time / 1000) % 60

        box.append($('<h1>Song Complete!</h1>'))
        if (random) {
            box.append($('<p>The mystery song was</p>'))
            box.append($(`<h2>${song_title}</h2>`))
        }
        box.append($(`<p>You completed this song in ${minutes}m ${seconds}s</p>`))

        var buttonGroup = $('<div>').addClass('buttonGroup')
        buttonGroup.append($(`<a href="/play/${song_id}">Play Again</a>`).addClass('dark'))
        buttonGroup.append($(`<a href="/random/${collection_id}">Play another random song in ${collection_title}</a>`))
        buttonGroup.append($(`<a href="/collection/${collection_id}">View all songs in ${collection_title}</a>`))
        box.append(buttonGroup)
    } else if (type === 'multiplayer complete') {
        const { time, random, winner, song_title } = data
        var minutes = Math.floor(time / 60000)
        var seconds = Math.floor(time / 1000) % 60

        box.append($('<h1>Song Complete!</h1>'))
        if (random) {
            box.append($('<p>The mystery song was</p>').addClass('mystery'))
            box.append($(`<h2>${song_title}</h2>`))
        }
        box.append($(`<p>${winner} completed this song in ${minutes}m ${seconds}s</p>`))
        box.append($('<div>').addClass('members dark'))

        var buttonGroup = $('<div>').addClass('buttonGroup')
        buttonGroup.append($(`<a href="/room">Back to Rooms</a>`).addClass('dark'))
        box.append(buttonGroup)
    } else if (type === 'disconnected') {
        box.append($('<h1>Disconnected</h1>'))
        box.append($('<p>You have been disconnected :(</p>'))

        var buttonGroup = $('<div>').addClass('buttonGroup')
        buttonGroup.append($(`<a href="/room">Back to Rooms</a>`).addClass('dark'))
        box.append(buttonGroup)
    } else if (type === 'multiplayer start') {
        const { random, song_title, collection_title, can_start, clickFunc } = data


        box.append($('<h1>Ready to start</h1>'))
        box.append($(`<p>You are playing ${random ? 'a random song' : song_title} from ${collection_title}</p>`))
        box.append($('<div>').addClass('members dark'))

        if (can_start) {
            var buttonGroup = $('<div>').addClass('buttonGroup')
            buttonGroup.append($(`<a>Start!</a>`).addClass('dark').click(clickFunc))
            box.append(buttonGroup)
        }
    }

    $('.popup').append(box)
    $('.popup').removeClass('hidden')
}

function closePopup() {
    $('.popup').addClass('hidden').empty()
}

function displayMembers(members, started) {
    $('.members').empty()
    members.sort(function (a, b) { return b.numerator - a.numerator }).forEach(function (member) {
        var percentage = (member.denominator === 0 ? 0 : Math.floor((member.numerator / member.denominator) * 100))
        console.log(`<div id="${member.id}">${member.username}${started ? ` ${percentage}%` : ''}</div>`)
        $('.members').append($(`<div id="${member.id}">${member.username}${started ? ` ${percentage}%` : ''}</div>`).addClass('member'))
    })
}

$(document).ready(function () {
    $('.collection').click(() => {
        $(this).toggleClass('expanded')
    })
})