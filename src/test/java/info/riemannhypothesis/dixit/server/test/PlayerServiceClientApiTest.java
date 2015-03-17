package info.riemannhypothesis.dixit.server.test;

import info.riemannhypothesis.dixit.server.client.ImageServiceApi;
import info.riemannhypothesis.dixit.server.client.MatchServiceApi;
import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.objects.Round;

import java.io.File;
import java.util.HashSet;
import java.util.Set;

import org.junit.Assert;
import org.junit.Test;

import retrofit.RestAdapter;
import retrofit.RestAdapter.LogLevel;
import retrofit.mime.TypedFile;

import com.google.appengine.api.datastore.Key;

public class PlayerServiceClientApiTest {

    public final static String  TEST_URL      = "http://localhost:8181";
    public final static String  LIVE_URL      = "http://dixit-app.appspot.com";

    private final static String URL           = TEST_URL;

    private PlayerServiceApi    playerService = new RestAdapter.Builder()
                                                      .setEndpoint(URL)
                                                      .setLogLevel(
                                                              LogLevel.FULL)
                                                      .build()
                                                      .create(PlayerServiceApi.class);
    private MatchServiceApi     matchService  = new RestAdapter.Builder()
                                                      .setEndpoint(URL)
                                                      .setLogLevel(
                                                              LogLevel.FULL)
                                                      .build()
                                                      .create(MatchServiceApi.class);
    private ImageServiceApi     imageService  = new RestAdapter.Builder()
                                                      .setEndpoint(URL)
                                                      .setLogLevel(
                                                              LogLevel.FULL)
                                                      .build()
                                                      .create(ImageServiceApi.class);

    private Player[]            players       = new Player[] {
            new Player("mk.schepke@gmail.com", "Markus"),
            new Player("test1@test.com", "Test1"),
            new Player("test2@test.com", "Test2"),
            new Player("test3@test.com", "Test3") };

    @Test
    public void test01players() throws Exception {
        Set<Long> playerKeys = new HashSet<Long>();

        for (int i = 0; i < players.length; i++) {
            Player player = players[i];
            player = playerService.addPlayer(player);
            players[i] = player;
            playerKeys.add(player.getKey().getId());
        }

        Match match = matchService.addMatch(playerKeys);

        Assert.assertTrue(false);

        for (int r = 0; r < match.getTotalRounds(); r++) {
            Round thisRound = match.getRounds().get(r);
            Key storyTellerId = thisRound.getStoryTellerKey();
            // Player storyTeller =
            // playerService.getPlayer(storyTellerId.getId());

            // String fileName = "image" + storyTellerId.getId();
            imageService.submitImage(new TypedFile("image/*", new File(
                    getClass().getResource("/pic.jpg").toURI())), storyTellerId
                    .getId(), match.getKey().getId(), r, "story " + r);

            for (Player player : players) {
                /* if (player.equals(storyTeller)) { continue; } */
                try {
                    // fileName = "image" + player.getKey().getId();
                    imageService.submitImage(new TypedFile("image/*", new File(
                            getClass().getResource("/pic.jpg").toURI())),
                            player.getKey().getId(), match.getKey().getId(), r,
                            null);
                } catch (Exception e) {
                    e.printStackTrace(System.err);
                }
            }

            match = matchService.getMatch(match.getKey().getId());
            thisRound = match.getRounds().get(r);

            for (int i = 0; i < players.length; i++) {
                Player player = players[i];
                /* if (player.equals(storyTeller)) { continue; } */
                try {
                    imageService.submitVote(
                            player.getKey().getId(),
                            match.getKey().getId(),
                            r,
                            thisRound.getImages().get(
                                    players[(i + 1) % players.length].getKey()
                                            .getId()));
                } catch (Exception e) {
                    e.printStackTrace(System.err);
                }
            }
        }
    }

}
