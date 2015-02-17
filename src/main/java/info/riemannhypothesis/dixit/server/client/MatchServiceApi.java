package info.riemannhypothesis.dixit.server.client;

import info.riemannhypothesis.dixit.server.objects.Match;

import java.util.Set;

import retrofit.http.Body;
import retrofit.http.GET;
import retrofit.http.POST;
import retrofit.http.Path;

import com.google.appengine.api.datastore.Key;

public interface MatchServiceApi {

    public static final String PATH = "/match";

    @POST(PATH)
    public Match addMatch(@Body Set<Long> keys);

    @GET(PATH)
    public Iterable<Match> getMatchList();

    @GET(PATH + "/{key}")
    public Match getMatch(@Path("key") Key key);

}
