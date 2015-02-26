package info.riemannhypothesis.dixit.server.controller;

import info.riemannhypothesis.dixit.server.Application;
import info.riemannhypothesis.dixit.server.client.ImageServiceApi;
import info.riemannhypothesis.dixit.server.objects.Image;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Round;
import info.riemannhypothesis.dixit.server.objects.Round.Status;
import info.riemannhypothesis.dixit.server.repository.ImageRepository;
import info.riemannhypothesis.dixit.server.repository.JDOCrudRepository.Callback;
import info.riemannhypothesis.dixit.server.repository.MatchRepository;
import info.riemannhypothesis.dixit.server.util.RequestUtils;
import info.riemannhypothesis.dixit.server.util.RequestUtils.RequestFields;
import info.riemannhypothesis.dixit.server.util.Utils;

import java.io.IOException;
import java.io.OutputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.channels.Channels;
import java.util.Random;

import javax.servlet.http.HttpServletRequest;

import org.apache.commons.fileupload.FileUploadException;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import retrofit.mime.TypedFile;

import com.google.appengine.api.datastore.KeyFactory;
import com.google.appengine.tools.cloudstorage.GcsFileOptions;
import com.google.appengine.tools.cloudstorage.GcsFilename;
import com.google.appengine.tools.cloudstorage.GcsOutputChannel;
import com.google.appengine.tools.cloudstorage.GcsService;
import com.google.appengine.tools.cloudstorage.GcsServiceFactory;
import com.google.appengine.tools.cloudstorage.RetryParams;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
@Controller
public class ImageService implements ImageServiceApi {

    @Autowired
    private MatchRepository     matches;
    @Autowired
    private ImageRepository     images;

    private final static Random RANDOM     = new Random();

    private final GcsService    gcsService = GcsServiceFactory
                                                   .createGcsService(new RetryParams.Builder()
                                                           .initialRetryDelayMillis(
                                                                   10)
                                                           .retryMaxAttempts(10)
                                                           .totalRetryPeriodMillis(
                                                                   15000)
                                                           .build());

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
    public URL submitImage(TypedFile file, long playerId, long matchId,
            int roundNum, String story) {
        try {
            return submitImage(IOUtils.toByteArray(file.in()), playerId,
                    matchId, roundNum, story);
        } catch (IOException e) {
            throw new IllegalArgumentException(e);
        }
    }

    @RequestMapping(value = IMAGE_SVC_PATH, method = RequestMethod.POST, produces = "application/json")
    public @ResponseBody URL submitImage(HttpServletRequest req)
            throws FileUploadException, IOException {
        RequestFields rf = RequestUtils.getRequestFields(req);

        byte[] imageBytes = rf.fileFields.get(IMAGE_PARAMETER);
        long playerId = Long.parseLong(rf.formFields.get(PLAYER_PARAMETER), 10);
        long matchId = Long.parseLong(rf.formFields.get(MATCH_PARAMETER), 10);
        int roundNum = Integer.parseInt(rf.formFields.get(ROUND_PARAMETER), 10);
        String story = rf.formFields.get(STORY_PARAMETER);

        return submitImage(imageBytes, playerId, matchId, roundNum, story);
    }

    public URL submitImage(final byte[] imageBytes, final long playerId,
            final long matchId, final int roundNum, final String story) {

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

                Image image = new Image(playerId);
                final String path = "image/" + playerId + "/"
                        + Math.abs(RANDOM.nextInt()) + ".jpg";

                try {
                    GcsFilename filename = new GcsFilename(
                            Application.GCS_BUCKET, path);

                    GcsFileOptions fileOptions = new GcsFileOptions.Builder()
                            .mimeType("image/jpeg")
                            .addUserMetadata("user",
                                    Long.toString(playerId, 10)).build();

                    GcsOutputChannel outputChannel = gcsService
                            .createOrReplace(filename, fileOptions);
                    OutputStream os = Channels.newOutputStream(outputChannel);
                    os.write(imageBytes);
                    os.close();
                } catch (IOException e) {
                    throw new IllegalArgumentException(e);
                }

                try {
                    URL url = new URL("http://storage.googleapis.com/"
                            + Application.GCS_BUCKET + "/" + path);
                    image.setUrl(url);
                } catch (MalformedURLException e) {
                    throw new IllegalStateException(e);
                }

                image = images.save(image);

                round.getImages().put(playerId, image.getKey().getId());
                round.getImageToPlayer().put(image.getKey().getId(), playerId);

                if (round.getStatus() == Status.SUBMIT_STORY) {
                    round.setStatus(Status.SUBMIT_OTHERS);
                } else if (round.submissionComplete()) {
                    round.setStatus(Status.SUBMIT_VOTES);
                }

                match.setLastModified(Utils.now());
            }
        };

        Match match = matches.update(KeyFactory.createKey("Match", matchId),
                callback);

        Round round = match.getRounds().get(roundNum);
        long imageId = round.getImages().get(playerId);
        return getImage(imageId).getUrl();
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
