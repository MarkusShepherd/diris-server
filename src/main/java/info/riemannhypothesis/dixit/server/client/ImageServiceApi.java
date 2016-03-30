package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Image;

import java.net.URL;
import java.util.List;

import retrofit.http.GET;
import retrofit.http.Multipart;
import retrofit.http.POST;
import retrofit.http.Part;
import retrofit.http.Path;
import retrofit.http.Query;
import retrofit.mime.TypedFile;

/**
 * @author Markus Schepke
 * @date 16 Feb 2015
 */
public interface ImageServiceApi {

	public static final String IMAGE_SVC_PATH = "/image";
	public static final String VOTE_SVC_PATH = "/vote";

	public static final String FILE_PARAMETER = "file";
	public static final String MATCH_PARAMETER = "match";
	public static final String ROUND_PARAMETER = "round";
	public static final String STORY_PARAMETER = "story";
	public static final String IMAGE_PARAMETER = "image";
	public static final String PLAYER_PARAMETER = "player";

	@GET(IMAGE_SVC_PATH)
	public List<Image> getImageList();

	@GET(IMAGE_SVC_PATH + "/{id}")
	public Image getImage(@Path("id") long id);

	@Multipart
	@POST(IMAGE_SVC_PATH)
	public URL submitImage(@Part(IMAGE_PARAMETER) TypedFile file,
			@Part(PLAYER_PARAMETER) long playerId,
			@Part(MATCH_PARAMETER) long matchId,
			@Part(ROUND_PARAMETER) int roundNum,
			@Part(STORY_PARAMETER) String story);

	@GET(VOTE_SVC_PATH)
	public boolean submitVote(@Query(PLAYER_PARAMETER) long playerId,
			@Query(MATCH_PARAMETER) long matchId,
			@Query(ROUND_PARAMETER) int roundNum,
			@Query(IMAGE_PARAMETER) long imageId);

}
