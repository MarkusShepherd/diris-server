package info.riemannhypothesis.dixit.server.repository;

import info.riemannhypothesis.dixit.server.objects.Image;

import org.springframework.stereotype.Service;

import com.google.appengine.api.datastore.Key;

/**
 * @author Markus Schepke
 * @date 17 Feb 2015
 */
@Service
public class ImageRepository extends JDOCrudRepository<Image, Key> {

    public ImageRepository() {
        super(Image.class);
    }

}
