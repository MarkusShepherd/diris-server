package info.riemannhypothesis.dixit.server.test;

import static org.junit.Assert.assertTrue;
import info.riemannhypothesis.dixit.server.client.PlayerServiceApi;
import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;

import org.junit.Test;

import retrofit.RestAdapter;
import retrofit.RestAdapter.LogLevel;

public class PlayerServiceClientApiTest {

    private final String     TEST_URL      = "http://localhost:8080";

    private PlayerServiceApi playerService = new RestAdapter.Builder()
                                                   .setEndpoint(TEST_URL)
                                                   .setLogLevel(LogLevel.FULL)
                                                   .build()
                                                   .create(PlayerServiceApi.class);

    private Player           player        = new Player("mk.schepke@gmail.com",
                                                   "Markus");

    @Test
    public void testVideoAddAndList() throws Exception {

        playerService.addPlayer(player);

        Collection<Player> videos = playerService.getPlayerList();
        assertTrue(videos.contains(player));
    }

}
