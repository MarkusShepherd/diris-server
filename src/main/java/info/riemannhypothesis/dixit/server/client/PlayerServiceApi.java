package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.List;

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

    @GET(PATH + "/id/{id}")
    public Player getPlayer(@Path("id") long id);

    @GET(PATH + "/email/{email}")
    public Player getPlayerByEmail(@Path("email") String email);

    @GET(PATH + "/name/{name}")
    public List<Player> getPlayerByName(@Path("name") String name);

}
