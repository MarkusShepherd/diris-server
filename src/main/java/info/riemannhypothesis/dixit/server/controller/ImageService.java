package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.client.ImageServiceApi;
import info.riemannhypothesis.dixit.server.objects.Image;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Round;
import info.riemannhypothesis.dixit.server.objects.Round.Status;
import info.riemannhypothesis.dixit.server.repository.ImageRepository;
import info.riemannhypothesis.dixit.server.repository.JDOCrudRepository.Callback;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import com.google.appengine.api.datastore.KeyFactory;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
@Controller
public class ImageService implements ImageServiceApi {

    @Autowired
    private MatchRepository matches;
    @Autowired
    private ImageRepository images;

    @Override
    @RequestMapping(value = IMAGE_SVC_PATH, method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Iterable<Image> getImageList() {
        return images.findAll();
    }

    @Override
    @RequestMapping(value = IMAGE_SVC_PATH + "/{id}", method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody Image getImage(@PathVariable("id") long id) {
        return images.findOne(KeyFactory.createKey("Image", id));
    }

    @Override
    @RequestMapping(value = IMAGE_SVC_PATH, method = RequestMethod.POST, produces = "application/json")
    public @ResponseBody boolean submitImage(
            @RequestBody String file,
            @RequestParam(value = PLAYER_PARAMETER, required = true) final long playerId,
            @RequestParam(value = MATCH_PARAMETER, required = true) final long matchId,
            @RequestParam(value = ROUND_PARAMETER, required = true) final int roundNum,
            @RequestParam(value = STORY_PARAMETER, defaultValue = "") final String story) {
        Callback<Match> callback = new Callback<Match>() {
            @Override
            public void apply(Match match) {
                Round round = match.getRounds().get(roundNum);

                if (round.getStatus() != Status.SUBMIT_STORY
                        && round.getStatus() != Status.SUBMIT_OTHERS) {
                    throw new IllegalArgumentException("Status "
                            + round.getStatus() + "; not expecting image.");
                }

                if (round.getStatus() == Status.SUBMIT_STORY) {
                    if (round.getStoryTellerKey().getId() != playerId) {
                        throw new IllegalArgumentException("Player " + playerId
                                + " is not the storyteller.");
                    }

                    if (story == null || story.length() == 0) {
                        throw new IllegalArgumentException(
                                "Storyteller must submit a story.");
                    }

                    round.setStory(story);
                } else {
                    if (round.getStoryTellerKey().getId() == playerId) {
                        throw new IllegalArgumentException(
                                "Player "
                                        + playerId
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

                image = images.save(image);

                System.out.println(getClass() + "; " + image.getKey());
                System.out.println(getClass() + "; " + round.getImages());

                round.getImages().put(playerId, image.getKey().getId());
                round.getImageToPlayer().put(image.getKey().getId(), playerId);

                if (round.getStatus() == Status.SUBMIT_STORY) {
                    round.setStatus(Status.SUBMIT_OTHERS);
                } else if (round.submissionComplete()) {
                    round.setStatus(Status.SUBMIT_VOTES);
                }
            }
        };

        matches.update(KeyFactory.createKey("Match", matchId), callback);

        return true;
    }

    @Override
    @RequestMapping(value = VOTE_SVC_PATH, method = RequestMethod.GET, produces = "application/json")
    public @ResponseBody boolean submitVote(
            @RequestParam(value = PLAYER_PARAMETER, required = true) final long playerId,
            @RequestParam(value = MATCH_PARAMETER, required = true) final long matchId,
            @RequestParam(value = ROUND_PARAMETER, required = true) final int roundNum,
            @RequestParam(value = IMAGE_PARAMETER, required = true) final long imageId) {

        Callback<Match> callback = new Callback<Match>() {
            @Override
            public void apply(Match match) {
                Round round = match.getRounds().get(roundNum);

                if (round.getStatus() != Status.SUBMIT_VOTES) {
                    throw new IllegalArgumentException("Status "
                            + round.getStatus() + "; not expecting votes.");
                }

                if (round.getStoryTellerKey().getId() == playerId) {
                    throw new IllegalArgumentException("Player " + playerId
                            + " is the storyteller and cannot submit a vote.");
                }

                if (!round.getImages().containsValue(imageId)) {
                    throw new IllegalArgumentException("Image " + imageId
                            + " not found in match " + matchId + ", round "
                            + roundNum + ".");
                }

                if (round.getImages().get(playerId).equals(imageId)) {
                    throw new IllegalArgumentException("Player " + playerId
                            + " cannot vote for their own image " + imageId
                            + ", match " + matchId + ", round " + roundNum
                            + ".");
                }

                if (round.getVotes().containsKey(playerId)) {
                    throw new IllegalArgumentException("Player " + playerId
                            + " has already voted" + ", match " + matchId
                            + ", round " + roundNum + ".");
                }

                round.getVotes().put(playerId, imageId);

                round.calculateScores();
            }
        };

        matches.update(KeyFactory.createKey("Match", matchId), callback);

        return true;
    }

}
