package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerServiceApi {

    public static final String PLAYER_SVC_PATH = "/player";

    @GET(PLAYER_SVC_PATH)
    public Collection<Player> getPlayerList();

    @GET(PLAYER_SVC_PATH + "/{id}")
    public Player getPlayer(@Path("id") long id);

    @POST(PLAYER_SVC_PATH)
    public boolean addPlayer(@Body Player player);

}
