package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.Player;

import java.util.Collection;

import org.springframework.web.bind.annotation.PathVariable;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerServiceApi {

    public static final String PLAYER_SVC_PATH = "/player";

    @GET(PLAYER_SVC_PATH)
    public Collection<Player> getPlayerList();

    @GET(PLAYER_SVC_PATH + "/{player}")
    public Player getPlayer(@PathVariable long player);

    @POST(PLAYER_SVC_PATH)
    public Void addPlayer(@Body Player player);

}
