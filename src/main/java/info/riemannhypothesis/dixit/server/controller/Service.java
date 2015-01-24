package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.ServiceApi;
import info.riemannhypothesis.dixit.server.objects.Image;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.objects.Round;
import info.riemannhypothesis.dixit.server.objects.Round.Status;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import java.util.Collection;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
@Controller
public class Service implements ServiceApi {

    @Autowired
    private PlayerRepository playerRepo;
    @Autowired
    private MatchRepository  matchRepo;

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH, method = RequestMethod.GET)
    public @ResponseBody Collection<Player> getPlayerList() {
        return playerRepo.getPlayers();
    }

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH + "/{id}", method = RequestMethod.GET)
    public @ResponseBody Player getPlayer(@PathVariable("id") long id) {
        return playerRepo.getPlayer(id);
    }

    @Override
    @RequestMapping(value = PLAYER_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean addPlayer(@RequestBody Player player) {
        return playerRepo.addPlayer(player);
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH, method = RequestMethod.GET)
    public @ResponseBody Collection<Match> getMatchList() {
        return matchRepo.getMatches();
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH + "/{id}", method = RequestMethod.GET)
    public @ResponseBody Match getMatch(@PathVariable("id") long id) {
        return matchRepo.getMatch(id);
    }

    @Override
    @RequestMapping(value = MATCH_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody long addMatch(@RequestBody long[] ids) {

        Match match = new Match(ids);
        matchRepo.addMatch(match);

        Player[] players = new Player[ids.length];
        for (int i = 0; i < players.length; i++) {
            players[i] = playerRepo.getPlayer(ids[i]);
        }

        for (int i = 0; i < players.length; i++) {
            players[i].addMatch(match);
        }

        return match.getId();
    }

    @Override
    @RequestMapping(value = IMAGE_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody String submitImage(
            /* @RequestBody MultipartFile file, */
            @RequestParam(value = PLAYER_PARAMETER, required = true) long playerId,
            @RequestParam(value = MATCH_PARAMETER, required = true) long matchId,
            @RequestParam(value = ROUND_PARAMETER, required = true) int roundNum,
            @RequestParam(value = STORY_PARAMETER, defaultValue = "") String story) {

        Match match = matchRepo.getMatch(matchId);
        Round round = match.getRounds()[roundNum];

        int playerPos = match.getPlayerPos(playerId);

        if (playerPos < 0) {
            throw new IllegalArgumentException("Player " + playerId
                    + " not found in match " + matchId + ".");
        }

        if (round.getStatus() != Status.SUBMIT_STORY
                && round.getStatus() != Status.SUBMIT_OTHERS) {
            throw new IllegalArgumentException("Status " + round.getStatus()
                    + "; not expecting image.");
        }

        if (round.getStatus() == Status.SUBMIT_STORY) {
            if (round.getStoryTellerId() != playerId) {
                throw new IllegalArgumentException("Player " + playerId
                        + " is not the storyteller.");
            }

            if (story == null || story.length() == 0) {
                throw new IllegalArgumentException(
                        "Storyteller must submit a story.");
            }

            round.setStory(story);
        } else {
            if (round.getStoryTellerId() == playerId) {
                throw new IllegalArgumentException("Player " + playerId
                        + " is the storyteller and cannot submit again.");
            }
        }

        Image image = new Image();
        final String path = /* file.getOriginalFilename() */"path";

        /* try { MultipartFile file = uploadItem; String fileName = null;
         * InputStream inputStream = null; OutputStream outputStream = null; if
         * (file.getSize() > 0) { inputStream = file.getInputStream(); if
         * (file.getSize() > 10000) { System.out.println("File Size:::" +
         * file.getSize()); return "/uploadfile"; } System.out.println("size::"
         * + file.getSize()); fileName = request.getRealPath("") + "/images/" +
         * file.getOriginalFilename(); outputStream = new
         * FileOutputStream(fileName); System.out.println("fileName:" +
         * file.getOriginalFilename());
         * 
         * int readBytes = 0; byte[] buffer = new byte[10000]; while ((readBytes
         * = inputStream.read(buffer, 0, 10000)) != -1) {
         * outputStream.write(buffer, 0, readBytes); } outputStream.close();
         * inputStream.close(); }
         * 
         * // ..........................................
         * session.setAttribute("uploadFile", file.getOriginalFilename()); }
         * catch (Exception e) { e.printStackTrace(); } */

        image.setPath(path);

        round.getImages()[playerPos] = image;

        if (round.getStatus() == Status.SUBMIT_STORY) {
            round.setStatus(Status.SUBMIT_OTHERS);
        } else if (round.submissionComplete()) {
            round.setStatus(Status.SUBMIT_VOTES);
        }

        return path;
    }

    @Override
    @RequestMapping(value = VOTE_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean submitVote(
            @RequestParam(value = PLAYER_PARAMETER, required = true) long playerId,
            @RequestParam(value = MATCH_PARAMETER, required = true) long matchId,
            @RequestParam(value = ROUND_PARAMETER, required = true) int roundNum,
            @RequestParam(value = IMAGE_PARAMETER, required = true) long imageId) {

        Match match = matchRepo.getMatch(matchId);
        Round round = match.getRounds()[roundNum];

        int playerPos = match.getPlayerPos(playerId);

        if (playerPos < 0) {
            throw new IllegalArgumentException("Player " + playerId
                    + " not found in match " + matchId + ".");
        }

        if (round.getStatus() != Status.SUBMIT_VOTES) {
            throw new IllegalArgumentException("Status " + round.getStatus()
                    + "; not expecting votes.");
        }

        if (round.getStoryTellerId() == playerId) {
            throw new IllegalArgumentException("Player " + playerId
                    + " is the storyteller and cannot submit a vote.");
        }

        int imagePos = round.getImagePos(imageId);

        if (imagePos < 0) {
            throw new IllegalArgumentException("Image " + imageId
                    + " not found in match " + matchId + ", round " + roundNum
                    + ".");
        }

        if (imagePos == playerPos) {
            throw new IllegalArgumentException("Player " + playerId
                    + " cannot vote for their own image " + imageId
                    + ", match " + matchId + ", round " + roundNum + ".");
        }

        round.getVotes()[playerPos] = imagePos;

        round.calculateScores();

        return true;
    }
}
