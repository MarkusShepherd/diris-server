package info.riemannhypothesis.dixit.server.objects;

/**
 * @author Markus Schepke
 * @date 18 Jan 2015
 */
public class Image {

    private long   id;

    private String path;

    public Image() {
        id = (long) (Math.random() * Long.MAX_VALUE);
    }

    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getPath() {
        return path;
    }

    public void setPath(String path) {
        this.path = path;
    }
}
