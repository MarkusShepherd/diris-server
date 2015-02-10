package info.riemannhypothesis.dixit.server.test;

import static org.junit.Assert.assertTrue;
import info.riemannhypothesis.dixit.server.client.ServiceApi;
import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;
import info.riemannhypothesis.dixit.server.objects.Round;

import java.util.Collection;

import org.junit.FixMethodOrder;
import org.junit.Test;
import org.junit.runners.MethodSorters;

import retrofit.RestAdapter;
import retrofit.RestAdapter.LogLevel;

@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class PlayerServiceClientApiTest {

    private final String TEST_URL = "http://localhost:8080";

    private ServiceApi   service  = new RestAdapter.Builder()
                                          .setEndpoint(TEST_URL)
                                          .setLogLevel(LogLevel.FULL).build()
                                          .create(ServiceApi.class);

    private Player[]     players  = new Player[] {
            new Player("mk.schepke@gmail.com", "Markus"),
            new Player("test1@test.com", "Test1"),
            new Player("test2@test.com", "Test2"),
            new Player("test3@test.com", "Test3") };

    @Test
    public void test01players() throws Exception {
        /*int c = 0;
        for (Player player : players) {
            player.setId(c++);
            service.addPlayer(player);
        }

        Collection<Player> videos = service.getPlayerList();
        for (Player player : players) {
            assertTrue(videos.contains(player));
        }

        long[] ids = new long[players.length];
        for (int i = 0; i < ids.length; i++) {
            ids[i] = players[i].getId();
        }

        long matchId = service.addMatch(ids);

        Match newMatch = service.getMatch(matchId);
        assertTrue(newMatch != null);

        for (int r = 0; r < newMatch.getTotalRounds(); r++) {
            Round thisRound = newMatch.getRounds()[r];
            long storyTellerId = thisRound.getStoryTellerId();
            Player storyTeller = service.getPlayer(storyTellerId);

            service.submitImage(storyTellerId, matchId, r, "story " + r);

            for (Player player : players) {
                if (player.equals(storyTeller)) {
                    continue;
                }
                service.submitImage(player.getId(), matchId, r, null);
            }

            newMatch = service.getMatch(matchId);
            for (int i = 0; i < players.length; i++) {
                Player player = players[i];
                if (player.equals(storyTeller)) {
                    continue;
                }
                service.submitVote(player.getId(), matchId, r,
                        newMatch.getRounds()[r].getImages()[(i + 1)
                                % players.length].getId());
            }
        }*/
    }

}
