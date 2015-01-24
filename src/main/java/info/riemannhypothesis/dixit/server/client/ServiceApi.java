package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Match;
import info.riemannhypothesis.dixit.server.objects.Player;

import java.util.Collection;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;
import retrofit.http.Query;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public interface ServiceApi {

    public static final String PLAYER_SVC_PATH  = "/player";
    public static final String MATCH_SVC_PATH   = "/match";
    public static final String IMAGE_SVC_PATH   = "/image";
    public static final String VOTE_SVC_PATH    = "/vote";

    public static final String PLAYER_PARAMETER = "player";
    public static final String MATCH_PARAMETER  = "match";
    public static final String ROUND_PARAMETER  = "round";
    public static final String STORY_PARAMETER  = "story";
    public static final String IMAGE_PARAMETER  = "image";

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

    @POST(IMAGE_SVC_PATH)
    public String submitImage(/* @Body MultipartFile file, */
    @Query(PLAYER_PARAMETER) long playerId,
            @Query(MATCH_PARAMETER) long matchId,
            @Query(ROUND_PARAMETER) int roundNum,
            @Query(STORY_PARAMETER) String story);

    @POST(VOTE_SVC_PATH)
    public boolean submitVote(@Query(PLAYER_PARAMETER) long playerId,
            @Query(MATCH_PARAMETER) long matchId,
            @Query(ROUND_PARAMETER) int roundNum,
            @Query(IMAGE_PARAMETER) long imageId);

}
