package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Match;

import java.util.List;
import java.util.Set;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;

public interface MatchServiceApi {

    public static final String PATH = "/match";

    @POST(PATH)
    public Match addMatch(@Body Set<Long> keys);

    @GET(PATH)
    public List<Match> getMatchList();

    @GET(PATH + "/{id}")
    public Match getMatch(@Path("id") long id);

}
