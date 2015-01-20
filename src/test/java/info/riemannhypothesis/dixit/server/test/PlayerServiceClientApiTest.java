package info.riemannhypothesis.dixit.server.test;

import static org.junit.Assert.assertTrue;
import info.riemannhypothesis.dixit.server.client.ServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;

import org.junit.Test;

import retrofit.RestAdapter;
import retrofit.RestAdapter.LogLevel;

public class PlayerServiceClientApiTest {

    private final String     TEST_URL      = "http://localhost:8080";

    private ServiceApi playerService = new RestAdapter.Builder()
                                                   .setEndpoint(TEST_URL)
                                                   .setLogLevel(LogLevel.FULL)
                                                   .build()
                                                   .create(ServiceApi.class);

    private Player[]         players       = new Player[] {
            new Player("mk.schepke@gmail.com", "Markus"),
            new Player("test1@test.com", "Test1"),
            new Player("test2@test.com", "Test2"),
            new Player("test3@test.com", "Test3") };

    @Test
    public void testPlayerAndMatch() throws Exception {

        for (Player player : players) {
            playerService.addPlayer(player);
        }

        Collection<Player> videos = playerService.getPlayerList();
        for (Player player : players) {
            assertTrue(videos.contains(player));
        }

        long[] ids = new long[players.length];
        for (int i = 0; i < ids.length; i++) {
            ids[i] = players[i].getId();
        }

        long matchId = playerService.addMatch(ids);

        Match newMatch = playerService.getMatch(matchId);
        assertTrue(newMatch != null);
    }

}
