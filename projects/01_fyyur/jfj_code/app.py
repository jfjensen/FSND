#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import *
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import Venue, Artist, Show


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  # print('value: {} date: {} type: {} date__: {}'.format(value,date, type(date), date.date()))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return str(date)#babel.dates.format_datetime(date, format) ############################ !!!

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
 
  venues = Venue.query.all()
  cities = {(v.city, v.state) for v in venues}

  data = [{"city": c[0],
            "state": c[1], 
            "venues": [{"id": v.id, 
                        "name": v.name, 
                        "num_upcoming_shows": Show.query.filter_by(venue_id=v.id).filter(Show.start_time >= datetime.now()).count()
                        } 
                      for v in venues if v.city == c[0]]
          }
          for c in cities ]


  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_string = request.form.get('search_term','')

  search_result = Venue.query.filter(Venue.name.ilike('%'+ search_string +'%')).all()
  search_count = len(search_result)

  data = [{"id": s.id, 
            "name": s.name, 
            "num_upcoming_shows": Show.query.filter_by(venue_id=s.id).filter(Show.start_time >= datetime.now()).count()
          } 
          for s in search_result]

  response={
    "count": search_count,
    "data": data
    }


  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # Done: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.filter_by(id=venue_id).first_or_404()

  past_shows_query = Show.query.join(Artist, Show.artist_id == Artist.id)\
                .filter(Show.venue_id==venue_id)\
                .filter(Show.start_time < datetime.now())\
                .add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time)\
                .all()

  upcoming_shows_query = Show.query.join(Artist, Show.artist_id == Artist.id)\
                .filter(Show.venue_id==venue_id)\
                .filter(Show.start_time >= datetime.now())\
                .add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time)\
                .all()

  past_shows = [{"artist_id": q[1], 
                "artist_name": q[2], 
                "artist_image_link": q[3], 
                "start_time": str(q[4])} 
                for q in past_shows_query]
  upcoming_shows = [{"artist_id": q[1], 
                      "artist_name": q[2], 
                      "artist_image_link": q[3], 
                      "start_time": str(q[4])} 
                  for q in upcoming_shows_query]


  data={
      "id": venue_id,
      "name": venue.name,
      "genres": venue.genres.split(", "),
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # Done: insert form data as a new Venue record in the db, instead
  # Done: modify data to be the data object returned from db insertion

  error = False

  try:
    venue_request = request.form
    venue = Venue(name=venue_request['name'],
                genres=', '.join(venue_request.getlist('genres')),
                address=venue_request['address'],
                city=venue_request['city'],
                state=venue_request['state'],
                phone=venue_request['phone'],
                # website=venue_request['website'],
                facebook_link=venue_request['facebook_link'],
                # seeking_talent=venue_request['seeking_talent'],
                # seeking_description=venue_request['seeking_description'],
                image_link='https://dummyimage.com/600x400/000/fff.jpg&text='+venue_request['name']
      )
    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Done: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  success = True
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    success = False
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  return jsonify({'success':success})


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Done: replace with real data returned from querying the database

  artist_query = Artist.query.all()

  data = [{"id": a.id,
            "name": a.name} for a in artist_query]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Done: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_string = request.form.get('search_term','')

  search_result = Artist.query.filter(Artist.name.ilike('%'+ search_string +'%')).all()
  search_count = len(search_result)

  data = [{"id": s.id, 
            "name": s.name, 
            "num_upcoming_shows": Show.query.filter_by(artist_id=s.id).filter(Show.start_time >= datetime.now()).count()
          } 
          for s in search_result]

  response={
    "count": search_count,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # Done: replace with real venue data from the venues table, using venue_id

  artist = Artist.query.filter_by(id=artist_id).first_or_404()

  past_shows_query = Show.query.join(Venue, Show.venue_id == Venue.id)\
                .filter(Show.artist_id==artist_id)\
                .filter(Show.start_time < datetime.now())\
                .add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time)\
                .all()

  upcoming_shows_query = Show.query.join(Venue, Show.venue_id == Venue.id)\
                .filter(Show.artist_id==artist_id)\
                .filter(Show.start_time >= datetime.now())\
                .add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time)\
                .all()

  past_shows = [{"venue_id": q[1], 
                "venue_name": q[2], 
                "venue_image_link": q[3], 
                "start_time": str(q[4])} 
                for q in past_shows_query]
  upcoming_shows = [{"venue_id": q[1], 
                      "venue_name": q[2], 
                      "venue_image_link": q[3], 
                      "start_time": str(q[4])} 
                  for q in upcoming_shows_query]

  data={
      "id": artist_id,
      "name": artist.name,
      "genres": artist.genres.split(", "),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
    }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # Done: insert form data as a new Artist record in the db, instead

  error = False

  try:
    artist_request = request.form
    artist = Artist(name=artist_request['name'],
                genres=', '.join(artist_request.getlist('genres')),
                city=artist_request['city'],
                state=artist_request['state'],
                phone=artist_request['phone'],
                facebook_link=artist_request['facebook_link'],
                image_link='https://dummyimage.com/600x400/000/fff.jpg&text='+artist_request['name']
      )
    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # Done: replace with real venues data.

  show_query= Show.query.join(Venue, Show.venue_id == Venue.id)\
              .join(Artist, Show.artist_id == Artist.id)\
              .order_by(Show.start_time)\
              .add_columns(Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, Show.start_time)\
              .all()

  data = [{
    "venue_id": s[1],
    "venue_name": s[2],
    "artist_id": s[3],
    "artist_name": s[4],
    "artist_image_link": s[5],
    "start_time":str(s[6])
  } for s in show_query]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # Done: insert form data as a new Show record in the db, instead
  error = False

  try:
    show_request = request.form
    show = Show(artist_id=show_request['artist_id'],
                venue_id=show_request['venue_id'],
                start_time=show_request['start_time']
              )
    db.session.add(show)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    # Done: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
