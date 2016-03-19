package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.List;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;
import retrofit.http.Query;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface PlayerServiceApi {

    public static final String PATH = "/player";

    @POST(PATH)
    public Player addPlayer(@Body Player player);

    @GET(PATH)
    public List<Player> getPlayerList();

    @GET(PATH + "/id/{id}")
    public Player getPlayerById(@Path("id") long id);

    @GET(PATH + "/id/{id}/external")
    public Player getPlayerByExternalId(@Path("id") String id);

    @GET(PATH + "/email")
    public Player getPlayerByEmail(@Query("email") String email);

    @GET(PATH + "/name/{name}")
    public List<Player> getPlayerByName(@Path("name") String name);

    @GET(PATH + "/id/{id}/matches")
    public List<Match> getPlayerMatches(@Path("id") long id);

    @GET(PATH + "/id/{id}/matches/{status}")
    public List<Match> getPlayerMatches(@Path("id") long id,
            @Path("status") String status);

}
