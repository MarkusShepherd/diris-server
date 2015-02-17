package info.riemannhypothesis.dixit.server.test;

import info.riemannhypothesis.dixit.server.client.ImageServiceApi;
import info.riemannhypothesis.dixit.server.client.MatchServiceApi;
import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.objects.Round;

import java.util.HashSet;
import java.util.Set;

import org.junit.Test;

import retrofit.RestAdapter;
import retrofit.RestAdapter.LogLevel;

import com.google.appengine.api.datastore.Key;

public class PlayerServiceClientApiTest {

    private final String     TEST_URL      = "http://localhost:8181";

    private PlayerServiceApi playerService = new RestAdapter.Builder()
                                                   .setEndpoint(TEST_URL)
                                                   .setLogLevel(LogLevel.FULL)
                                                   .build()
                                                   .create(PlayerServiceApi.class);
    private MatchServiceApi  matchService  = new RestAdapter.Builder()
                                                   .setEndpoint(TEST_URL)
                                                   .setLogLevel(LogLevel.FULL)
                                                   .build()
                                                   .create(MatchServiceApi.class);
    private ImageServiceApi  imageService  = new RestAdapter.Builder()
                                                   .setEndpoint(TEST_URL)
                                                   .setLogLevel(LogLevel.FULL)
                                                   .build()
                                                   .create(ImageServiceApi.class);

    private Player[]         players       = new Player[] {
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

        for (int r = 0; r < match.getTotalRounds(); r++) {
            Round thisRound = match.getRounds().get(r);
            Key storyTellerId = thisRound.getStoryTellerKey();
            Player storyTeller = playerService.getPlayer(storyTellerId);

            imageService.submitImage(storyTellerId, match.getKey(), r, "story "
                    + r);

            for (Player player : players) {
                if (player.equals(storyTeller)) {
                    continue;
                }
                imageService.submitImage(player.getKey(), match.getKey(), r,
                        null);
            }

            Match newMatch = matchService.getMatch(match.getKey());

            for (int i = 0; i < players.length; i++) {
                Player player = players[i];
                if (player.equals(storyTeller)) {
                    continue;
                }
                imageService
                        .submitVote(
                                player.getKey(),
                                newMatch.getKey(),
                                r,
                                newMatch.getRounds()
                                        .get(r)
                                        .getImages()
                                        .get(players[(i + 1) % players.length]
                                                .getKey()));
            }
        }
    }

}
