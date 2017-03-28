'use strict';

function shuffle(o) {
    var j, x, i;
    for (i = o.length; i; j = Math.floor(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x) {}
    return o;
}

function processRound(round, player) {
    if (!round) {
        return round;
    }

    // round.details = $.filter(round.player_round_details || [],
    //                       function (details) { return !!(details && details.player === player.pk); })[0];

    round.detailsPlayers = {};
    round.votes = {};
    $.each(round.player_round_details, function (i, details) {
        round.detailsPlayers[details.player.toString()] = details;
        if (details.vote_player) {
            round.votes[details.vote_player] = round.votes[details.vote_player] || [];
            round.votes[details.vote_player].push(details.player.toString());
        }

        if (details.player == player.pk) {
            round.details = details;
        }
    });

    if (!round.details) {
        return round;
    }

    round.isStoryTeller = player.pk == round.storyteller;
    round.hasSubmittedImage = !!round.details.image && (!round.isStoryTeller || !!round.story);
    round.hasVoted = !!round.details.vote;

    round.readyForStoryImage = false;
    round.readyForOtherImage = false;
    round.readyForVote = false;

    if (round.status === 's' && round.isStoryTeller) {
        round.readyForStoryImage = true;
    } else if (round.status === 'o' && !round.isStoryTeller && !round.hasSubmittedImage) {
        round.readyForOtherImage = true;
    } else if (round.status === 'v' && !round.isStoryTeller && !round.hasVoted) {
        round.readyForVote = true;
    }

    round.hasAction = round.readyForStoryImage || round.readyForOtherImage || round.readyForVote;

    round.scores = {};
    round.scoresArray = $.map(round.player_round_details, function (details) {
        round.scores[details.player.toString()] = details.score;
        return {
            playerPk: details.player,
            score: details.score
        };
    });

    return round;
}

function processMatch(match, player) {
    match.rounds = $.map(match.rounds, function (round) {
        return processRound(round, player);
    });
    match.currentRoundObj = match.rounds[(match.current_round || 1) - 1];

    // match.details = $.filter(match.player_match_details || [],
    //                       function (details) { return !!(details && details.player === player.pk); })[0];
    match.accepted = {};
    $.each(match.player_match_details, function (i, details) {
        match.accepted[details.player.toString()] = details.invitation_status === 'a';
        if (details.player == player.pk) {
            match.details = details;
        }
    });

    var score = match.details ? match.details.score : 0,
        pos = 1;

    $.each(match.player_match_details, function (i, details) {
        if (details.score > score) {
            pos++;
        }
    });

    match.playerPosition = pos;
    match.playerPositionOrd = getOrdinal(pos);

    match.scores = {};
    match.standingsArray = $.map(match.player_match_details, function (details) {
        match.scores[details.player.toString()] = details.score;
        return {
            playerPk: details.player,
            score: details.score
        };
    });

    match.createdFromNow = moment(match.created).fromNow();
    match.lastModifiedFromNow = moment(match.last_modified).fromNow();

    match.hasAccepted = match.details && match.details.invitation_status === 'a';

    return match;
}

function getOrdinal(n) {
    var s = ['th', 'st', 'nd', 'rd'],
        v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function isBrowser() {
    try {
        return device && device.platform === 'browser';
    } catch (err) {
        return true;
    }
}
