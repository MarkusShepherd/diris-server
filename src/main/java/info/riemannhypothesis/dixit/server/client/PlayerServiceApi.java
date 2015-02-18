package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Player;
import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerServiceApi {

    public static final String PATH = "/player";

    @POST(PATH)
    public Player addPlayer(@Body Player player);

    @GET(PATH)
    public Iterable<Player> getPlayerList();

    @GET(PATH + "/{id}")
    public Player getPlayer(@Path("id") long id);

}
