function getSong(song_id) {
    $.ajax({
        url: '/api/getSong/' + song_id,
        cache: false,
        dataType: 'json',
        success: play,
    })
}

function play(data) {
    $('.title').text(data.song.title)
    $('.collection').text(data.collection.title)
    $('.collection').attr('href', '/collection/' + data.collection._id.$oid)

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
            }
        })
    })
}

$(document).ready(function () {
    $('.collection').click(() => {
        $(this).toggleClass('expanded')
    })
})