package info.riemannhypothesis.dixit.server.client;

import retrofit.http.POST;
import retrofit.http.Query;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
public interface ImageServiceApi {

    public static final String IMAGE_SVC_PATH   = "/image";
    public static final String VOTE_SVC_PATH    = "/vote";

    public static final String MATCH_PARAMETER  = "match";
    public static final String ROUND_PARAMETER  = "round";
    public static final String STORY_PARAMETER  = "story";
    public static final String IMAGE_PARAMETER  = "image";
    public static final String PLAYER_PARAMETER = "player";

    @POST(IMAGE_SVC_PATH)
    public boolean submitImage(/* @Body MultipartFile file, */
    @Query(PLAYER_PARAMETER) Key playerKey,
            @Query(MATCH_PARAMETER) Key matchKey,
            @Query(ROUND_PARAMETER) int roundNum,
            @Query(STORY_PARAMETER) String story);

    @POST(VOTE_SVC_PATH)
    public boolean submitVote(@Query(PLAYER_PARAMETER) Key playerKey,
            @Query(MATCH_PARAMETER) Key matchKey,
            @Query(ROUND_PARAMETER) int roundNum,
            @Query(IMAGE_PARAMETER) Key imageKey);

}
