package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Match;
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
public interface ServiceApi {

    public static final String PLAYER_SVC_PATH = "/player";
    public static final String MATCH_SVC_PATH  = "/match";

    @GET(PLAYER_SVC_PATH)
    public Collection<Player> getPlayerList();

    @GET(PLAYER_SVC_PATH + "/{id}")
    public Player getPlayer(@Path("id") long id);

    @POST(PLAYER_SVC_PATH)
    public boolean addPlayer(@Body Player player);

    @GET(MATCH_SVC_PATH)
    public Collection<Match> getMatchList();

    @GET(MATCH_SVC_PATH + "/{id}")
    public Match getMatch(@Path("id") long id);

    @POST(MATCH_SVC_PATH)
    public long addMatch(@Body long[] ids);

}
