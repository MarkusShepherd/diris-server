function shuffle(o) {
	for (var j, x, i = o.length; i; j = Math.floor(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x)
		;
	return o;
}

function processRound(round, player) {
	if (!round)
		return round;

	round.isStoryTeller = player.key.id === round.storyTellerKey.id;
	round.hasSubmittedImage = player.key.id in round.images;
	round.hasVoted = player.key.id in round.votes;

	round.readyForStoryImage = false;
	round.readyForOtherImage = false;
	round.readyForVote = false;

	if (round.status === 'SUBMIT_STORY' && round.isStoryTeller)
		round.readyForStoryImage = true;
	else if (round.status === 'SUBMIT_OTHERS' && !round.isStoryTeller && !round.hasSubmittedImage)
		round.readyForOtherImage = true;
	else if (round.status === 'SUBMIT_VOTES' && !round.isStoryTeller && !round.hasVoted)
		round.readyForVote = true;

	round.hasAction = round.readyForStoryImage || round.readyForOtherImage || round.readyForVote;

	round.scoresArray = $.map(round.scores, function(s, pId) {
		return {
			playerId: pId,
			score: s
		};
	});

	return round;
}

function processMatch(match, player) {
	match.rounds = $.map(match.rounds, function(round) {
		return processRound(round, player);
	});
	match.currentRoundObj = match.rounds[match.currentRound];

	var score = match.standings[player.key.id];
	var pos = 1;
	$.each(match.standings, function(k, v) {
		if (v > score)
			pos++;
	});
	match.playerPosition = pos;
	match.playerPositionOrd = getOrdinal(pos);

	match.standingsArray = $.map(match.standings, function(s, pId) {
		return {
			playerId: pId,
			score: s
		};
	});

	match.createdFromNow = moment(match.created).fromNow();
	match.lastModifiedFromNow = moment(match.lastModified).fromNow();

	match.hasAccepted = !!(match.status != "WAITING" || match.accepted[player.key.id]);

	return match;
}

function getOrdinal(n) {
   var s=["th","st","nd","rd"],
       v=n%100;
   return n+(s[(v-20)%10]||s[v]||s[0]);
}

function isBrowser() {
	try {
		return device && device.platform === 'browser';
	} catch (err) {
		return true;
	}
}