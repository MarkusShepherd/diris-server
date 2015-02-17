package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.ImageServiceApi;
import info.riemannhypothesis.dixit.server.objects.Image;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Round;
import info.riemannhypothesis.dixit.server.objects.Round.Status;
import info.riemannhypothesis.dixit.server.repository.JDOCrudRepository.Callback;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.repository.PlayerRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
@Controller
public class ImageService implements ImageServiceApi {

    @Autowired
    private MatchRepository  matches;
    @Autowired
    private PlayerRepository players;

    @Override
    @RequestMapping(value = IMAGE_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean submitImage(
            /* @RequestBody MultipartFile file, */
            @RequestParam(value = PLAYER_PARAMETER, required = true) final Key playerKey,
            @RequestParam(value = MATCH_PARAMETER, required = true) final Key matchKey,
            @RequestParam(value = ROUND_PARAMETER, required = true) final int roundNum,
            @RequestParam(value = STORY_PARAMETER, defaultValue = "") final String story) {
        Callback<Match> callback = new Callback<Match>() {
            @Override
            public void apply(Match match) {
                Round round = match.getRounds().get(roundNum);

                int playerPos = match.getPlayerPos(playerKey);

                if (playerPos < 0) {
                    throw new IllegalArgumentException("Player " + playerKey
                            + " not found in match " + matchKey + ".");
                }

                if (round.getStatus() != Status.SUBMIT_STORY
                        && round.getStatus() != Status.SUBMIT_OTHERS) {
                    throw new IllegalArgumentException("Status "
                            + round.getStatus() + "; not expecting image.");
                }

                if (round.getStatus() == Status.SUBMIT_STORY) {
                    if (!round.getStoryTellerKey().equals(playerKey)) {
                        throw new IllegalArgumentException("Player "
                                + playerKey + " is not the storyteller.");
                    }

                    if (story == null || story.length() == 0) {
                        throw new IllegalArgumentException(
                                "Storyteller must submit a story.");
                    }

                    round.setStory(story);
                } else {
                    if (round.getStoryTellerKey().equals(playerKey)) {
                        throw new IllegalArgumentException(
                                "Player "
                                        + playerKey
                                        + " is the storyteller and cannot submit again.");
                    }
                }

                Image image = new Image();
                final String path = /* file.getOriginalFilename() */"path";

                /* try { MultipartFile file = uploadItem; String fileName =
                 * null; InputStream inputStream = null; OutputStream
                 * outputStream = null; if (file.getSize() > 0) { inputStream =
                 * file.getInputStream(); if (file.getSize() > 10000) {
                 * System.out.println("File Size:::" + file.getSize()); return
                 * "/uploadfile"; } System.out.println("size::" +
                 * file.getSize()); fileName = request.getRealPath("") +
                 * "/images/" + file.getOriginalFilename(); outputStream = new
                 * FileOutputStream(fileName); System.out.println("fileName:" +
                 * file.getOriginalFilename());
                 * 
                 * int readBytes = 0; byte[] buffer = new byte[10000]; while
                 * ((readBytes = inputStream.read(buffer, 0, 10000)) != -1) {
                 * outputStream.write(buffer, 0, readBytes); }
                 * outputStream.close(); inputStream.close(); }
                 * 
                 * // ..........................................
                 * session.setAttribute("uploadFile",
                 * file.getOriginalFilename()); } catch (Exception e) {
                 * e.printStackTrace(); } */

                image.setPath(path);

                round.getImages().put(playerKey, image.getKey());

                if (round.getStatus() == Status.SUBMIT_STORY) {
                    round.setStatus(Status.SUBMIT_OTHERS);
                } else if (round.submissionComplete()) {
                    round.setStatus(Status.SUBMIT_VOTES);
                }
            }
        };

        matches.update(matchKey, callback);

        return true;
    }

    @Override
    @RequestMapping(value = VOTE_SVC_PATH, method = RequestMethod.POST)
    public @ResponseBody boolean submitVote(
            @RequestParam(value = PLAYER_PARAMETER, required = true) final Key playerKey,
            @RequestParam(value = MATCH_PARAMETER, required = true) final Key matchKey,
            @RequestParam(value = ROUND_PARAMETER, required = true) final int roundNum,
            @RequestParam(value = IMAGE_PARAMETER, required = true) final Key imageKey) {

        Callback<Match> callback = new Callback<Match>() {
            @Override
            public void apply(Match match) {
                Round round = match.getRounds().get(roundNum);

                int playerPos = match.getPlayerPos(playerKey);

                if (playerPos < 0) {
                    throw new IllegalArgumentException("Player " + playerKey
                            + " not found in match " + matchKey + ".");
                }

                if (round.getStatus() != Status.SUBMIT_VOTES) {
                    throw new IllegalArgumentException("Status "
                            + round.getStatus() + "; not expecting votes.");
                }

                if (round.getStoryTellerKey().equals(playerKey)) {
                    throw new IllegalArgumentException("Player " + playerKey
                            + " is the storyteller and cannot submit a vote.");
                }

                if (!round.getImages().containsValue(imageKey)) {
                    throw new IllegalArgumentException("Image " + imageKey
                            + " not found in match " + matchKey + ", round "
                            + roundNum + ".");
                }

                if (round.getImages().get(playerKey).equals(imageKey)) {
                    throw new IllegalArgumentException("Player " + playerKey
                            + " cannot vote for their own image " + imageKey
                            + ", match " + matchKey + ", round " + roundNum
                            + ".");
                }

                if (round.getVotes().containsKey(playerKey)) {
                    throw new IllegalArgumentException("Player " + playerKey
                            + " has already voted" + ", match " + matchKey
                            + ", round " + roundNum + ".");
                }

                round.getVotes().put(playerKey, imageKey);

                round.calculateScores();
            }
        };

        matches.update(matchKey, callback);

        return true;
    }
}
